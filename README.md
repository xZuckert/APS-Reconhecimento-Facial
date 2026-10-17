# VerdeID — integração do frontend com a API

O `index.html` original foi preservado em seu layout e conteúdo principal. A integração troca somente o login simulado por autenticação real via API e acrescenta a exibição dos registros ambientais retornados pelo backend.

## O que foi integrado

- `GET /` entrega `index.html` pela mesma origem da API.
- O botão de acesso chama `POST /reconhecimento`, `POST /sessao`, `GET /status` e `GET /dados/{nivel}`.
- O nível exibido vem do usuário autenticado no banco; a interface não permite escolher um nível para entrar.
- O botão “Sair” invalida a sessão no backend com `DELETE /sessao`.
- `GET /cadastro/foto/{foto_id}` entrega fotos temporárias criadas por `/cadastro/foto`.
- A seção “Informações ambientais da API” exibe com segurança (via `textContent`) os registros devolvidos pelo endpoint protegido. Os artigos, mapas e gráficos existentes continuam sendo conteúdo demonstrativo do frontend.

## Estrutura esperada

```text
VerdeID-integrado/
├── index.html
├── inicializacao.sql
├── compose.yaml
└── src/
    ├── __init__.py
    ├── api.py
    ├── main.py
    └── ...
```

## Executar

1. Copie os arquivos para a estrutura equivalente do seu projeto, mantendo o ambiente virtual já existente.
2. Configure o `.env` conforme os nomes esperados pelo `compose.yaml` e por `src/banco_dados.py`. Não compartilhe esse arquivo nem credenciais.
3. Garanta que o PostgreSQL esteja ativo e que o banco tenha sido inicializado com `inicializacao.sql`.
4. Na raiz do projeto, ative sua `.venv` e execute:

```bash
PYTHONPATH=.:src python -m src.main
```

5. Acesse `http://127.0.0.1:8000`. A câmera precisa estar disponível para o processo que executa `src/main.py`, e o usuário precisa estar cadastrado com foto no banco.

## Limitações conhecidas

- A tela usa a câmera compartilhada pelo processo Python; não solicita acesso direto à webcam do navegador.
- A autenticação depende do endpoint de reconhecimento já existente e do estado recente produzido por ele.
- Os conteúdos editoriais, gráficos e pontos do mapa do HTML continuam identificados como material de demonstração; somente a lista “Informações ambientais da API” vem do banco pela rota protegida.
- Os testes originais do projeto ainda não foram recebidos nesta etapa. Rode-os após substituir os arquivos e envie a pasta `tests/` para que eu possa verificar compatibilidade com a integração.
