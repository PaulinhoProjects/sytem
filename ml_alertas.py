import logging
from datetime import datetime, timedelta
import numpy as np
from models_alertas import Alerta, PredictaoProducao, ScoreLavoura

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLAlertas:
    def __init__(self, db):
        self.db = db

    def detectar_anomalias(self, lavoura_id):
        """Detecta anomalias em produção usando média móvel e desvio padrão"""
        from models import Producao, Lavoura
        
        # Buscar últimas 30 produções
        producoes = self.db.session.query(Producao).filter(
            Producao.lavoura_id == lavoura_id
        ).order_by(Producao.data_colheita.desc()).limit(30).all()

        if len(producoes) < 5:
            logger.info(f'Insuficientes dados para lavoura {lavoura_id}')
            return []

        quantidades = np.array([p.quantidade_kg for p in reversed(producoes)])
        media_historica = np.mean(quantidades)
        desvio_padrao = np.std(quantidades)
        ultima_producao = quantidades[-1]

        anomalias = []

        # Queda > 20% vs média
        if ultima_producao < media_historica * 0.8:
            anomalias.append({
                'tipo': 'Queda Crítica de Produção',
                'severidade': 'CRÍTICO',
                'mensagem': f'Produção de KG caiu {((1 - ultima_producao/media_historica)*100):.1f}% em relação ao seu histórico',
                'sugestao': 'Verificar deficiência nutricional, pragas foliares e doenças imediatamente.'
            })
            logger.warning(f'Anomalia crítica detectada em lavoura {lavoura_id}')

        # Queda > 10% vs média
        elif ultima_producao < media_historica * 0.9:
            anomalias.append({
                'tipo': 'Queda de Produção',
                'severidade': 'AVISO',
                'mensagem': f'Volume de Prod. caiu {((1 - ultima_producao/media_historica)*100):.1f}% vs média histórica',
                'sugestao': 'Acompanhamento da irrigação e condições hidricas urgentes.'
            })

        # Desvio muito alto
        if ultima_producao < media_historica - 1.5 * desvio_padrao:
            anomalias.append({
                'tipo': 'Desvio Anômalo de Operação',
                'severidade': 'AVISO',
                'mensagem': f'Queda de {1.5:.1f} desvios padrão abaixo da constância da lavoura',
                'sugestao': 'Análise da qualidade do solo recomendada (Macro e Micronutrientes).'
            })

        return anomalias

    def prever_producao(self, lavoura_id):
        """Prevê produção para próximo mês usando regressão linear simples (ML Baseline)"""
        from models import Producao
        
        producoes = self.db.session.query(Producao).filter(
            Producao.lavoura_id == lavoura_id
        ).order_by(Producao.data_colheita.asc()).limit(12).all()

        if len(producoes) < 3:
            logger.info(f'Dados insuficientes para previsão estatística em lavoura {lavoura_id}')
            return {
                'mes_previsto': (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m'),
                'quantidade_estimada': 0,
                'confianca': 0.0
            }

        # Regressão linear
        x = np.arange(len(producoes))
        y = np.array([p.quantidade_kg for p in producoes])
        
        coef = np.polyfit(x, y, 1)
        slope = coef[0]
        intercept = coef[1]
        
        # Previsão para próximo período
        next_x = len(producoes)
        quantidade_estimada = slope * next_x + intercept
        quantidade_estimada = max(0, quantidade_estimada)  # Não pode ser negativo
        
        # Calcular confiança baseada em R²
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        confianca = max(0, min(1, r_squared))

        logger.info(f'Forecast Lavoura {lavoura_id}: {quantidade_estimada:.2f} kg com {confianca*100:.1f}% probabilidade (R2)')

        return {
            'mes_previsto': (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m'),
            'quantidade_estimada': float(quantidade_estimada),
            'confianca': float(confianca)
        }

    def calcular_score_saude(self, lavoura_id):
        """Calcula score algorítmico de saúde (0-100)"""
        from models import Producao
        
        producoes = self.db.session.query(Producao).filter(
            Producao.lavoura_id == lavoura_id
        ).order_by(Producao.data_colheita.desc()).limit(10).all()

        if not producoes:
            return 50, 'sem_dados'

        producoes = list(reversed(producoes))
        quantidades = [p.quantidade_kg for p in producoes]
        
        media_recente = np.mean(quantidades[-3:]) if len(quantidades) >= 3 else quantidades[-1]
        media_geral = np.mean(quantidades)
        
        score = (media_recente / media_geral * 100) if media_geral > 0 else 50
        score = max(0, min(100, score))

        # Tendência
        if len(quantidades) >= 2:
            tendencia_calc = quantidades[-1] - quantidades[-2]
            if tendencia_calc > media_geral * 0.05:
                tendencia = 'melhorando'
            elif tendencia_calc < -media_geral * 0.05:
                tendencia = 'piorando'
            else:
                tendencia = 'estavel'
        else:
            tendencia = 'estavel'

        logger.info(f'Scoring Machine Lavoura {lavoura_id}: {score:.1f}/100 - TS: {tendencia}')

        return float(score), tendencia

    def processar_alertas_produtor(self, produtor_id):
        """Macro-job para reprocessar ML Metrics para todo o produtor"""
        from models import Lavoura
        
        lavouras = self.db.session.query(Lavoura).filter(
            Lavoura.produtor_id == produtor_id
        ).all()

        alertas_criados = 0

        for lavoura in lavouras:
            # 1. Detectar anomalias produtivas (Regressão e Histórico)
            anomalias = self.detectar_anomalias(lavoura.id)
            for anom in anomalias:
                alerta_existente = self.db.session.query(Alerta).filter(
                    Alerta.lavoura_id == lavoura.id,
                    Alerta.tipo == anom['tipo'],
                    Alerta.resolvido == False
                ).first()

                if not alerta_existente:
                    alerta = Alerta(
                        tipo=anom['tipo'],
                        severidade=anom['severidade'],
                        produtor_id=produtor_id,
                        lavoura_id=lavoura.id,
                        mensagem=f"{anom['mensagem']} | Sugestão: {anom['sugestao']}"
                    )
                    self.db.session.add(alerta)
                    alertas_criados += 1

            # 2. Atualizar Forecast (Regressão Linear)
            previsao = self.prever_producao(lavoura.id)
            pred_existente = self.db.session.query(PredictaoProducao).filter(
                PredictaoProducao.lavoura_id == lavoura.id,
                PredictaoProducao.mes_previsto == previsao['mes_previsto']
            ).first()

            if not pred_existente:
                pred = PredictaoProducao(
                    lavoura_id=lavoura.id,
                    mes_previsto=previsao['mes_previsto'],
                    quantidade_estimada=previsao['quantidade_estimada'],
                    confianca=previsao['confianca']
                )
                self.db.session.add(pred)

            # 3. Atualizar Health Score Estatístico
            score, tendencia = self.calcular_score_saude(lavoura.id)
            score_obj = ScoreLavoura(
                lavoura_id=lavoura.id,
                score_saude=score,
                tendencia=tendencia
            )
            self.db.session.add(score_obj)

        self.db.session.commit()
        logger.info(f'Processamento Massivo Feito. {alertas_criados} novos alertas ML instanciados para o produtor_id: {produtor_id}')

        return alertas_criados
