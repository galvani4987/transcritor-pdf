# -*- coding: utf-8 -*-
"""
Ponto de entrada principal para a aplicação CLI Transcritor PDF.

Orquestra o fluxo: carregar -> pré-processar -> extrair -> apresentar.
"""

# (Importaremos os módulos aqui quando existirem)
# from .input_handler import load_document
# from .preprocessor import preprocess_document
# from .extractor import extract_information
# from .output_handler import format_output

def run_transcription_pipeline(file_path: str):
    """
    Executa o pipeline completo de processamento para um arquivo.

    Args:
        file_path: O caminho para o arquivo de imagem ou PDF a ser processado.
    """
    print(f"Iniciando processamento para: {file_path}")

    # 1. Carregar o documento (Input Handler)
    # document_data = load_document(file_path)
    print("-> (Placeholder) Documento carregado.")

    # 2. Pré-processar o documento (Preprocessor)
    # processed_data = preprocess_document(document_data)
    print("-> (Placeholder) Documento pré-processado.")

    # 3. Extrair informações (Extractor)
    # extracted_info = extract_information(processed_data)
    print("-> (Placeholder) Informações extraídas.")

    # 4. Formatar e apresentar a saída (Output Handler)
    # output = format_output(extracted_info)
    # print(output)
    print("-> (Placeholder) Saída formatada.")

    print("Processamento concluído.")

def main_cli():
    """
    Função principal que lida com os argumentos da linha de comando.
    """
    # Usaremos argparse ou outra biblioteca CLI aqui futuramente
    # para pegar o caminho do arquivo do usuário.
    print("--- Transcritor PDF ---")
    # Por enquanto, vamos simular um caminho de arquivo
    example_file = "exemplo_documento.jpg" # Simulação
    run_transcription_pipeline(example_file)

if __name__ == "__main__":
    # Este bloco é executado quando o script é chamado diretamente (ex: python src/main.py)
    main_cli()