from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Produtor, Lavoura, Usuario
from models.pulverizacao import (
    ProdutoPulverizacao, Praga, OcorrenciaPraga,
    CronogramaPulverizacao, AplicacaoPulverizacao,
    StatusAplicacao, SeveridadePraga
)
from utils import role_required
import logging
import os
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)
pulverizacao_bp = Blueprint('pulverizacao', __name__, url_prefix='/pulverizacao')

UPLOAD_FOLDER = 'uploads/pragas'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ============ HELPER FUNCTIONS ============

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verificar_acesso_pulverizacao(produtor_id):
    """Verifica se o usuário tem acesso às pulverizações do produtor"""
    papel = current_user.role
    if papel == 'ADM':
        return True
    if papel == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        return produtor and produtor.id == produtor_id
    if papel in ('AGRONOMA', 'AGRONOMO'):
        produtor = Produtor.query.get(produtor_id)
        return produtor and produtor.agronomist_id == current_user.id
    return False

# ============ ROTAS PRODUTOS PULVERIZACAO ============

@pulverizacao_bp.route('/produtos', methods=['GET'])
@login_required
@role_required('ADM', 'AGRONOMA')
def listar_produtos_pulverizacao():
    """Lista todos os produtos de pulverizacao"""
    page = request.args.get('page', 1, type=int)
    tipo_filtro = request.args.get('tipo', None)
    
    query = ProdutoPulverizacao.query.filter_by(ativo=True)
    
    if tipo_filtro:
        query = query.filter_by(tipo=tipo_filtro)
    
    produtos = query.paginate(page=page, per_page=15)
    tipos = ['inseticida', 'fungicida', 'herbicida', 'acaricida']
    
    return render_template('pulverizacao/produtos.html', produtos=produtos, tipos=tipos, tipo_selecionado=tipo_filtro)

@pulverizacao_bp.route('/produto/criar', methods=['GET', 'POST'])
@login_required
@role_required('ADM')
def criar_produto_pulverizacao():
    """Cria um novo produto de pulverizacao"""
    tipos = ['inseticida', 'fungicida', 'herbicida', 'acaricida']
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            ingrediente_ativo = request.form.get('ingrediente_ativo', '').strip()
            tipo = request.form.get('tipo')
            concentracao = request.form.get('concentracao', '').strip()
            dose_recomendada = request.form.get('dose_recomendada', '').strip()
            unidade_dose = request.form.get('unidade_dose', 'ml')
            fabricante = request.form.get('fabricante', '').strip()
            registro_mapa = request.form.get('registro_mapa', '').strip()
            periodo_carencia = request.form.get('periodo_carencia', 0, type=int)
            descricao = request.form.get('descricao', '').strip()
            
            if not all([nome, tipo]):
                flash('Nome e tipo são obrigatórios.', 'error')
                return redirect(url_for('pulverizacao.criar_produto_pulverizacao'))
            
            produto_existente = ProdutoPulverizacao.query.filter_by(nome=nome).first()
            if produto_existente:
                flash('Produto com este nome já existe.', 'error')
                return redirect(url_for('pulverizacao.criar_produto_pulverizacao'))
            
            produto = ProdutoPulverizacao(
                nome=nome,
                ingrediente_ativo=ingrediente_ativo,
                tipo=tipo,
                concentracao=concentracao,
                dose_recomendada=dose_recomendada,
                unidade_dose=unidade_dose,
                fabricante=fabricante,
                registro_mapa=registro_mapa,
                periodo_carencia=periodo_carencia,
                descricao=descricao
            )
            db.session.add(produto)
            db.session.commit()
            
            logger.info(f'Produto pulverizacao criado: {nome} por {current_user.username}')
            flash('Produto criado com sucesso!', 'success')
            return redirect(url_for('pulverizacao.listar_produtos_pulverizacao'))
        
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar produto pulverizacao: {str(e)}')
            flash('Erro ao criar produto.', 'error')
            return redirect(url_for('pulverizacao.criar_produto_pulverizacao'))
    
    return render_template('pulverizacao/criar_produto.html', tipos=tipos)

@pulverizacao_bp.route('/produto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('ADM')
def editar_produto_pulverizacao(id):
    """Edita um produto de pulverizacao"""
    produto = ProdutoPulverizacao.query.get_or_404(id)
    tipos = ['inseticida', 'fungicida', 'herbicida', 'acaricida']
    
    if request.method == 'POST':
        try:
            produto.nome = request.form.get('nome', '').strip()
            produto.ingrediente_ativo = request.form.get('ingrediente_ativo', '').strip()
            produto.tipo = request.form.get('tipo')
            produto.concentracao = request.form.get('concentracao', '').strip()
            produto.dose_recomendada = request.form.get('dose_recomendada', '').strip()
            produto.unidade_dose = request.form.get('unidade_dose', 'ml')
            produto.fabricante = request.form.get('fabricante', '').strip()
            produto.registro_mapa = request.form.get('registro_mapa', '').strip()
            produto.periodo_carencia = request.form.get('periodo_carencia', 0, type=int)
            produto.descricao = request.form.get('descricao', '').strip()
            
            db.session.commit()
            
            logger.info(f'Produto pulverizacao atualizado: {produto.nome} por {current_user.username}')
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('pulverizacao.listar_produtos_pulverizacao'))
        
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao atualizar produto: {str(e)}')
            flash('Erro ao atualizar produto.', 'error')
    
    return render_template('pulverizacao/editar_produto.html', produto=produto, tipos=tipos)

# ============ ROTAS PRAGAS ============

@pulverizacao_bp.route('/pragas', methods=['GET'])
@login_required
@role_required('ADM', 'AGRONOMA')
def listar_pragas():
    """Lista todas as pragas cadastradas"""
    page = request.args.get('page', 1, type=int)
    tipo_filtro = request.args.get('tipo', None)
    
    query = Praga.query.filter_by(ativo=True)
    
    if tipo_filtro:
        query = query.filter_by(tipo=tipo_filtro)
    
    pragas = query.paginate(page=page, per_page=15)
    tipos = ['inseto', 'fungo', 'bacteria', 'virus', 'nematoide']
    
    return render_template('pulverizacao/pragas.html', pragas=pragas, tipos=tipos, tipo_selecionado=tipo_filtro)

@pulverizacao_bp.route('/praga/criar', methods=['GET', 'POST'])
@login_required
@role_required('ADM')
def criar_praga():
    """Cria uma nova praga"""
    tipos = ['inseto', 'fungo', 'bacteria', 'virus', 'nematoide']
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            nome_cientifico = request.form.get('nome_cientifico', '').strip()
            tipo = request.form.get('tipo')
            descricao = request.form.get('descricao', '').strip()
            dano_potencial = request.form.get('dano_potencial', '').strip()
            metodos_controle = request.form.get('metodos_controle', '').strip()
            
            if not all([nome, tipo]):
                flash('Nome e tipo são obrigatórios.', 'error')
                return redirect(url_for('pulverizacao.criar_praga'))
            
            praga_existente = Praga.query.filter_by(nome=nome).first()
            if praga_existente:
                flash('Praga com este nome já existe.', 'error')
                return redirect(url_for('pulverizacao.criar_praga'))
            
            praga = Praga(
                nome=nome,
                nome_cientifico=nome_cientifico,
                tipo=tipo,
                descricao=descricao,
                dano_potencial=dano_potencial,
                metodos_controle=metodos_controle
            )
            db.session.add(praga)
            db.session.commit()
            
            logger.info(f'Praga criada: {nome} por {current_user.username}')
            flash('Praga criada com sucesso!', 'success')
            return redirect(url_for('pulverizacao.listar_pragas'))
        
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar praga: {str(e)}')
            flash('Erro ao criar praga.', 'error')
            return redirect(url_for('pulverizacao.criar_praga'))
    
    return render_template('pulverizacao/criar_praga.html', tipos=tipos)

# ============ ROTAS OCORRÊNCIAS DE PRAGAS ============

@pulverizacao_bp.route('/ocorrencias', methods=['GET'])
@login_required
def listar_ocorrencias():
    """Lista ocorrências de pragas"""
    page = request.args.get('page', 1, type=int)
    
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        ocorrencias = OcorrenciaPraga.query.filter_by(
            produtor_id=produtor.id
        ).order_by(OcorrenciaPraga.data_deteccao.desc()).paginate(page=page, per_page=15)
    else:
        ocorrencias = OcorrenciaPraga.query.order_by(
            OcorrenciaPraga.data_deteccao.desc()
        ).paginate(page=page, per_page=15)
    
    return render_template('pulverizacao/ocorrencias.html', ocorrencias=ocorrencias)

@pulverizacao_bp.route('/ocorrencia/registrar', methods=['GET', 'POST'])
@login_required
@role_required('PRODUTOR', 'AGRONOMA')
def registrar_ocorrencia():
    """Registra uma nova ocorrência de praga"""
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor:
            flash('Nenhum produtor vinculado.', 'error')
            return redirect(url_for('dashboard'))
        lavouras = Lavoura.query.filter_by(produtor_id=produtor.id).all()
    else:
        lavouras = Lavoura.query.all()
    
    pragas = Praga.query.filter_by(ativo=True).all()
    severidades = ['baixa', 'media', 'alta', 'critica']
    
    if request.method == 'POST':
        try:
            lavoura_id = request.form.get('lavoura_id', type=int)
            praga_id = request.form.get('praga_id', type=int)
            severidade = request.form.get('severidade')
            percentual_infestacao = request.form.get('percentual_infestacao', 0, type=float)
            data_deteccao = datetime.strptime(request.form.get('data_deteccao'), '%Y-%m-%d').date()
            observacoes = request.form.get('observacoes', '').strip()
            
            if not all([lavoura_id, praga_id, severidade]):
                flash('Preencha todos os campos obrigatórios.', 'error')
                return redirect(url_for('pulverizacao.registrar_ocorrencia'))
            
            lavoura = Lavoura.query.get_or_404(lavoura_id)
            produtor_id = lavoura.produtor_id
            
            if not verificar_acesso_pulverizacao(produtor_id):
                flash('Você não tem acesso a esta lavoura.', 'error')
                return redirect(url_for('pulverizacao.registrar_ocorrencia'))
            
            # Processar foto se enviada
            foto_path = None
            if 'foto' in request.files:
                file = request.files['foto']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f'{datetime.utcnow().timestamp()}_{filename}'
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    foto_path = os.path.join(UPLOAD_FOLDER, filename)
            
            ocorrencia = OcorrenciaPraga(
                lavoura_id=lavoura_id,
                praga_id=praga_id,
                produtor_id=produtor_id,
                usuario_id=current_user.id,
                severidade=severidade,
                percentual_infestacao=percentual_infestacao,
                data_deteccao=data_deteccao,
                observacoes=observacoes,
                foto_path=foto_path
            )
            db.session.add(ocorrencia)
            db.session.commit()
            
            logger.info(f'Ocorrência de praga registrada: {praga_id} em lavoura {lavoura_id} por {current_user.username}')
            flash('Ocorrência registrada com sucesso!', 'success')
            return redirect(url_for('pulverizacao.listar_ocorrencias'))
        
        except ValueError as e:
            logger.error(f'Erro ao registrar ocorrência (valor): {str(e)}')
            flash('Erro ao processar data.', 'error')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao registrar ocorrência: {str(e)}')
            flash('Erro ao registrar ocorrência.', 'error')
            return redirect(url_for('pulverizacao.registrar_ocorrencia'))
    
    return render_template(
        'pulverizacao/registrar_ocorrencia.html',
        lavouras=lavouras,
        pragas=pragas,
        severidades=severidades
    )

# ============ ROTAS CRONOGRAMA PULVERIZACAO ============

@pulverizacao_bp.route('/cronogramas', methods=['GET'])
@login_required
def listar_cronogramas():
    """Lista cronogramas de pulverizacao"""
    page = request.args.get('page', 1, type=int)
    
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        cronogramas = CronogramaPulverizacao.query.filter_by(
            produtor_id=produtor.id
        ).order_by(CronogramaPulverizacao.data_planejada).paginate(page=page, per_page=10)
    else:
        cronogramas = CronogramaPulverizacao.query.order_by(
            CronogramaPulverizacao.data_planejada
        ).paginate(page=page, per_page=10)
    
    return render_template('pulverizacao/cronogramas.html', cronogramas=cronogramas)

@pulverizacao_bp.route('/cronograma/criar', methods=['GET', 'POST'])
@login_required
@role_required('AGRONOMA', 'ADM')
def criar_cronograma():
    """Cria um novo cronograma de pulverizacao"""
    lavouras = Lavoura.query.all()
    produtores = Produtor.query.all()
    
    if request.method == 'POST':
        try:
            lavoura_id = request.form.get('lavoura_id', type=int)
            produtor_id = request.form.get('produtor_id', type=int)
            titulo = request.form.get('titulo', '').strip()
            descricao = request.form.get('descricao', '').strip()
            data_planejada = datetime.strptime(request.form.get('data_planejada'), '%Y-%m-%d').date()
            observacoes = request.form.get('observacoes', '').strip()
            
            if not all([lavoura_id, produtor_id, titulo, data_planejada]):
                flash('Preencha todos os campos obrigatórios.', 'error')
                return redirect(url_for('pulverizacao.criar_cronograma'))
            
            cronograma = CronogramaPulverizacao(
                lavoura_id=lavoura_id,
                produtor_id=produtor_id,
                usuario_id=current_user.id,
                titulo=titulo,
                descricao=descricao,
                data_planejada=data_planejada,
                observacoes=observacoes,
                status='planejada'
            )
            db.session.add(cronograma)
            db.session.commit()
            
            logger.info(f'Cronograma criado: {titulo} por {current_user.username}')
            flash('Cronograma criado com sucesso!', 'success')
            return redirect(url_for('pulverizacao.listar_cronogramas'))
        
        except ValueError as e:
            logger.error(f'Erro ao criar cronograma (valor): {str(e)}')
            flash('Erro ao processar data.', 'error')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar cronograma: {str(e)}')
            flash('Erro ao criar cronograma.', 'error')
            return redirect(url_for('pulverizacao.criar_cronograma'))
    
    return render_template('pulverizacao/criar_cronograma.html', lavouras=lavouras, produtores=produtores)

@pulverizacao_bp.route('/cronograma/<int:id>/detalhes', methods=['GET'])
@login_required
def detalhes_cronograma(id):
    """Visualiza detalhes de um cronograma"""
    cronograma = CronogramaPulverizacao.query.get_or_404(id)
    
    if not verificar_acesso_pulverizacao(cronograma.produtor_id):
        flash('Acesso negado.', 'error')
        return redirect(url_for('pulverizacao.listar_cronogramas'))
    
    aplicacoes = AplicacaoPulverizacao.query.filter_by(cronograma_id=id).all()
    
    return render_template('pulverizacao/detalhes_cronograma.html', cronograma=cronograma, aplicacoes=aplicacoes)

# ============ ROTAS APLICAÇÕES PULVERIZACAO ============

@pulverizacao_bp.route('/aplicacao/criar', methods=['GET', 'POST'])
@login_required
@role_required('PRODUTOR', 'AGRONOMA')
def criar_aplicacao():
    """Registra uma nova aplicação de pulverizacao"""
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        lavouras = Lavoura.query.filter_by(produtor_id=produtor.id).all()
        cronogramas = CronogramaPulverizacao.query.filter_by(produtor_id=produtor.id).all()
    else:
        lavouras = Lavoura.query.all()
        cronogramas = CronogramaPulverizacao.query.all()
    
    produtos = ProdutoPulverizacao.query.filter_by(ativo=True).all()
    pragas = Praga.query.filter_by(ativo=True).all()
    eficacias = ['excelente', 'bom', 'regular', 'fraco']
    velocidades_vento = ['baixa', 'media', 'alta']
    condicoes_clima = ['ensolarado', 'nublado', 'chuvoso', 'parcialmente nublado']
    
    if request.method == 'POST':
        try:
            cronograma_id = request.form.get('cronograma_id', type=int)
            lavoura_id = request.form.get('lavoura_id', type=int)
            produto_id = request.form.get('produto_id', type=int)
            praga_id = request.form.get('praga_id', type=int, default=None)
            
            data_aplicacao = datetime.strptime(request.form.get('data_aplicacao'), '%Y-%m-%d').date()
            hora_inicio = request.form.get('hora_inicio')
            hora_fim = request.form.get('hora_fim')
            
            quantidade_aplicada = request.form.get('quantidade_aplicada', type=float)
            area_aplicada = request.form.get('area_aplicada', type=float)
            volume_calda = request.form.get('volume_calda', type=float, default=0)
            
            equipamento_utilizado = request.form.get('equipamento_utilizado', '').strip()
            condicoes_clima_str = request.form.get('condicoes_clima', '').strip()
            velocidade_vento = request.form.get('velocidade_vento', '').strip()
            temperatura = request.form.get('temperatura', type=float, default=0)
            umidade = request.form.get('umidade', type=float, default=0)
            
            aplicador_nome = request.form.get('aplicador_nome', '').strip()
            epi_utilizado = request.form.get('epi_utilizado', '').strip()
            eficacia = request.form.get('eficacia', '').strip()
            observacoes = request.form.get('observacoes', '').strip()
            
            if not all([cronograma_id, lavoura_id, produto_id, data_aplicacao, quantidade_aplicada, area_aplicada]):
                flash('Preencha todos os campos obrigatórios.', 'error')
                return redirect(url_for('pulverizacao.criar_aplicacao'))
            
            lavoura = Lavoura.query.get_or_404(lavoura_id)
            
            if not verificar_acesso_pulverizacao(lavoura.produtor_id):
                flash('Acesso negado.', 'error')
                return redirect(url_for('pulverizacao.criar_aplicacao'))
            
            aplicacao = AplicacaoPulverizacao(
                cronograma_id=cronograma_id,
                lavoura_id=lavoura_id,
                produtor_id=lavoura.produtor_id,
                usuario_id=current_user.id,
                produto_id=produto_id,
                praga_id=praga_id if praga_id else None,
                data_aplicacao=data_aplicacao,
                hora_inicio=datetime.strptime(hora_inicio, '%H:%M').time() if hora_inicio else None,
                hora_fim=datetime.strptime(hora_fim, '%H:%M').time() if hora_fim else None,
                quantidade_aplicada=quantidade_aplicada,
                area_aplicada=area_aplicada,
                volume_calda=volume_calda,
                equipamento_utilizado=equipamento_utilizado,
                condicoes_clima=condicoes_clima_str,
                velocidade_vento=velocidade_vento,
                temperatura=temperatura,
                umidade=umidade,
                aplicador_nome=aplicador_nome,
                epi_utilizado=epi_utilizado,
                eficacia=eficacia,
                observacoes=observacoes
            )
            db.session.add(aplicacao)
            db.session.commit()
            
            logger.info(f'Aplicação criada: {data_aplicacao} em lavoura {lavoura_id} por {current_user.username}')
            flash('Aplicação registrada com sucesso!', 'success')
            return redirect(url_for('pulverizacao.listar_cronogramas'))
        
        except ValueError as e:
            logger.error(f'Erro ao criar aplicação (valor): {str(e)}')
            flash('Erro ao processar data ou hora.', 'error')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar aplicação: {str(e)}')
            flash('Erro ao registrar aplicação.', 'error')
            return redirect(url_for('pulverizacao.criar_aplicacao'))
    
    return render_template(
        'pulverizacao/criar_aplicacao.html',
        lavouras=lavouras,
        cronogramas=cronogramas,
        produtos=produtos,
        pragas=pragas,
        eficacias=eficacias,
        velocidades_vento=velocidades_vento,
        condicoes_clima=condicoes_clima
    )

@pulverizacao_bp.route('/aplicacao/<int:id>/detalhes', methods=['GET'])
@login_required
def detalhes_aplicacao(id):
    """Visualiza detalhes de uma aplicação"""
    aplicacao = AplicacaoPulverizacao.query.get_or_404(id)
    
    if not verificar_acesso_pulverizacao(aplicacao.produtor_id):
        flash('Acesso negado.', 'error')
        return redirect(url_for('pulverizacao.listar_cronogramas'))
    
    dias_carencia = aplicacao.calcular_dias_carencia()
    
    return render_template('pulverizacao/detalhes_aplicacao.html', aplicacao=aplicacao, dias_carencia=dias_carencia)

# ============ ROTAS DASHBOARD PULVERIZACAO ============

@pulverizacao_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard_pulverizacao():
    """Dashboard com resumo de pulverizacoes"""
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor:
            flash('Nenhum produtor vinculado.', 'error')
            return redirect(url_for('dashboard'))
        
        ocorrencias_criticas = OcorrenciaPraga.query.filter_by(
            produtor_id=produtor.id,
            severidade='critica'
        ).count()
        
        aplicacoes_mes = AplicacaoPulverizacao.query.filter_by(
            produtor_id=produtor.id
        ).filter(
            AplicacaoPulverizacao.data_aplicacao >= datetime.utcnow().date().replace(day=1)
        ).count()
        
        cronogramas_pendentes = CronogramaPulverizacao.query.filter_by(
            produtor_id=produtor.id,
            status='planejada'
        ).count()
        
        aplicacoes_recentes = AplicacaoPulverizacao.query.filter_by(
            produtor_id=produtor.id
        ).order_by(AplicacaoPulverizacao.data_aplicacao.desc()).limit(5).all()
    else:
        ocorrencias_criticas = OcorrenciaPraga.query.filter_by(severidade='critica').count()
        aplicacoes_mes = AplicacaoPulverizacao.query.filter(
            AplicacaoPulverizacao.data_aplicacao >= datetime.utcnow().date().replace(day=1)
        ).count()
        cronogramas_pendentes = CronogramaPulverizacao.query.filter_by(status='planejada').count()
        aplicacoes_recentes = AplicacaoPulverizacao.query.order_by(
            AplicacaoPulverizacao.data_aplicacao.desc()
        ).limit(5).all()
    
    return render_template(
        'pulverizacao/dashboard.html',
        ocorrencias_criticas=ocorrencias_criticas,
        aplicacoes_mes=aplicacoes_mes,
        cronogramas_pendentes=cronogramas_pendentes,
        aplicacoes_recentes=aplicacoes_recentes
    )

# ============ ROTAS API (JSON) ============

@pulverizacao_bp.route('/api/praga/<int:id>', methods=['GET'])
@login_required
def api_praga(id):
    """Retorna dados JSON de uma praga"""
    praga = Praga.query.get_or_404(id)
    return jsonify(praga.to_dict())

@pulverizacao_bp.route('/api/produto/<int:id>', methods=['GET'])
@login_required
def api_produto_pulverizacao(id):
    """Retorna dados JSON de um produto de pulverizacao"""
    produto = ProdutoPulverizacao.query.get_or_404(id)
    return jsonify(produto.to_dict())

@pulverizacao_bp.route('/api/cronograma/<int:id>', methods=['GET'])
@login_required
def api_cronograma(id):
    """Retorna dados JSON de um cronograma"""
    cronograma = CronogramaPulverizacao.query.get_or_404(id)
    
    if not verificar_acesso_pulverizacao(cronograma.produtor_id):
        return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify(cronograma.to_dict())
