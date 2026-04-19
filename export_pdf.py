from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import matplotlib.pyplot as plt
import io as io_module
import matplotlib
matplotlib.use('Agg')
from datetime import datetime

class RelatorioGerador:
    def __init__(self, db):
        self.db = db

    def gerar_relatorio_producao(self, periodo_inicio, periodo_fim, produtor_id=None, lavoura_id=None):
        """Gera relatório de produção em PDF com gráficos e tabelas formatadas"""
        from models_alertas import PredictaoProducao
        
        query = self.db.session.query(PredictaoProducao).filter(
            PredictaoProducao.data_criacao.between(periodo_inicio, periodo_fim)
        )
        if lavoura_id:
            query = query.filter(PredictaoProducao.lavoura_id == lavoura_id)
        predictions = query.all()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Header
        story.append(Paragraph("Relatório de Produção Agrícola", styles['Heading1']))
        story.append(Paragraph(f"Período: {periodo_inicio.strftime('%d/%m/%Y')} a {periodo_fim.strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Table with data
        data = [['Lavoura ID', 'Mês Previsto', 'Quantidade Estimada (kg)', 'Confiança']]
        total_producao = 0
        for p in predictions:
            data.append([str(p.lavoura_id), p.mes_previsto, f"{p.quantidade_estimada:.2f} kg", f"{p.confianca*100:.1f}%"])
            total_producao += p.quantidade_estimada
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F5F5F5')),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')])
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        # Summary KPI
        story.append(Paragraph(f"<b>Volume Total Estimado: {total_producao:.2f} kg</b>", styles['Normal']))
        story.append(Spacer(1, 12))

        # Chart
        if predictions:
            fig, ax = plt.subplots(figsize=(8, 4))
            meses = [p.mes_previsto for p in predictions]
            quantidades = [p.quantidade_estimada for p in predictions]
            ax.bar(meses, quantidades, color='#4CAF50', edgecolor='#8B4513')
            ax.set_title('Produção Estimada por Mês', fontsize=14, fontweight='bold')
            ax.set_xlabel('Mês')
            ax.set_ylabel('Quantidade (kg)')
            ax.grid(axis='y', alpha=0.3)
            
            img_buffer = io_module.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            img = Image(img_buffer, width=6*inch, height=3*inch)
            story.append(img)
            plt.close(fig)

        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<i>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def gerar_relatorio_lavouras(self, periodo_inicio, periodo_fim, produtor_id=None):
        """Gera relatório de saúde das lavouras"""
        from models_alertas import ScoreLavoura
        
        query = self.db.session.query(ScoreLavoura).filter(
            ScoreLavoura.data_calculo.between(periodo_inicio, periodo_fim)
        )
        scores = query.all()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Relatório de Saúde das Lavouras", styles['Heading1']))
        story.append(Spacer(1, 12))

        data = [['Lavoura ID', 'Score Saúde', 'Tendência', 'Data Cálculo']]
        for s in scores:
            tendencia_emoji = '📈' if s.tendencia == 'melhorando' else '➡️' if s.tendencia == 'estavel' else '📉'
            data.append([
                str(s.lavoura_id), 
                f"{s.score_saude:.1f}/100", 
                f"{tendencia_emoji} {s.tendencia}", 
                s.data_calculo.strftime('%d/%m/%Y')
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8B4513')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F5F5F5')),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)

        doc.build(story)
        buffer.seek(0)
        return buffer

    def gerar_relatorio_agronomico(self, periodo_inicio, periodo_fim):
        """Gera relatório agronômico com alertas e recomendações"""
        from models_alertas import Alerta
        
        alerts = self.db.session.query(Alerta).filter(
            Alerta.data_criacao.between(periodo_inicio, periodo_fim)
        ).all()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Relatório Agronômico de Contingência", styles['Heading1']))
        story.append(Spacer(1, 12))

        data = [['Tipo', 'Severidade', 'Mensagem', 'Status', 'Data']]
        críticos = sum(1 for a in alerts if a.severidade == 'CRÍTICO')
        avisos = sum(1 for a in alerts if a.severidade == 'AVISO')
        
        for a in alerts:
            status = '✅ Resolvido' if a.resolvido else '⚠️ Pendente'
            data.append([
                a.tipo, 
                a.severidade, 
                a.mensagem[:40] + '...' if len(a.mensagem) > 40 else a.mensagem,
                status,
                a.data_criacao.strftime('%d/%m/%Y')
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FF9800')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F5F5F5')),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        story.append(Paragraph(f"<b>Resumo de Intervenções:</b> {críticos} alertas críticos | {avisos} avisos", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer
