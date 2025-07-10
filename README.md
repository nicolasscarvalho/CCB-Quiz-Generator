# 📖 Gerador de Provas de Inglês

Preciso, rápido e simples. Uma ferramenta de automação para gerar provas de inglês customizadas a partir de um banco de questões estruturado.

## O que é o projeto

Este projeto é uma aplicação web, construída com Streamlit, que serve como uma ferramenta para professores e coordenadores de cursos de inglês. O objetivo principal é automatizar e agilizar o processo de criação de provas, permitindo a seleção aleatória de questões a partir de um banco de dados local organizado em formato JSON.

O sistema oferece filtros por livro e unidades, além da configuração do número de questões por seção (Grammar, Vocabulary, Pronunciation), e gera como saída um arquivo `.docx` pronto para impressão, contendo a prova e uma folha de respostas ao final.

### Fluxograma do Usuário

O fluxo de uso da aplicação foi desenhado para ser simples e intuitivo:

1.  **Acessa a Aplicação:** O usuário abre a página da aplicação web.
2.  **Configuração na Barra Lateral:**
      * Seleciona o **Livro** desejado.
      * Filtra as **Unidades** em duas etapas: primeiro a(s) numérica(s) e depois a(s) sub-unidade(s) (A, B, C...).
      * Define a **quantidade de questões** para cada seção (Grammar, Vocabulary, Pronunciation).
3.  **Geração da Prova:**
      * O usuário visualiza um resumo da sua configuração.
      * Clica no botão "Gerar prova padrão" ou "Gerar prova customizada".
4.  **Download:**
      * Após o processamento, o botão "Baixar Prova (.docx)" é habilitado.
      * O usuário clica para baixar o arquivo `.docx` contendo a prova formatada e o gabarito em uma página separada.

## 🚀 Tecnologias Utilizadas

O projeto é construído primariamente em Python, com o auxílio de bibliotecas específicas para cada tarefa.

  * **Linguagem:**

      * `Python 3.x`

  * **Bibliotecas Principais:**

      * **`Streamlit`**: Para a construção de toda a interface web interativa da aplicação.
      * **`python-docx`**: Utilizada exclusivamente para a **criação e escrita** do arquivo de prova final no formato `.docx`.
      * **Bibliotecas Padrão**: O projeto utiliza bibliotecas nativas do Python como `json` (para ler e processar os arquivos de dados), `os` (para interagir com o sistema de arquivos e encontrar as pastas/questões) e `random` (para o sorteio das questões).

## 📁 Estrutura de Diretórios

Para que o programa funcione corretamente, o banco de questões deve seguir uma estrutura de pastas e uma convenção de nomenclatura rigorosas.

### Hierarquia das Pastas

A organização começa a partir de um diretório raiz chamado `BOOKS`. A partir dele, a estrutura é a seguinte:

BOOKS/  
└── NOME_DO_LIVRO/  
├── GRAMMAR/  
│   └── NOME_DA_PASTA_DA_UNIDADE/  
│       └── ARQUIVO_DE_QUESTAO.json  
├── VOCABULARY/  
│   └── NOME_DA_PASTA_DA_UNIDADE/  
│       └── ARQUIVO_DE_QUESTAO.json  
└── PRONUNCIATION/  
└── ...

- **`NOME_DO_LIVRO/`**: Cada livro do curso deve ter sua própria pasta. O nome desta pasta deve ser em maiúsculas (ex: `ELEMENTARY`).

- **`NOME_DA_SEÇÃO/`**: Dentro de cada livro, devem existir as três pastas de seção, nomeadas exatamente como `GRAMMAR`, `VOCABULARY`, e `PRONUNCIATION`.

- **`NOME_DA_PASTA_DA_UNIDADE/`**: Esta é a pasta que contém os arquivos de questão para uma unidade específica. Sua nomenclatura é crucial e segue o padrão: `NomeDoLivro_NomeDaSeção_Unit_Unidade`.
  - **Exemplo:** `Elementary_GRAMMAR_Unit_3A`

### Nomenclatura dos Arquivos JSON

Dentro de cada pasta de unidade, os arquivos de questões devem ser do formato `.json` e seguir o padrão: `NomeDaPastaDaUnidade_Questão_Numero.json`.

- **Exemplo:** `Elementary_GRAMMAR_Unit_3A_Questão_1.json`

## 📝 Estrutura dos Arquivos JSON

Para garantir a robustez e eliminar ambiguidades, o banco de questões abandonou o formato `.docx` e utiliza exclusivamente arquivos `.json`. A estrutura de pastas permanece a mesma, mas os arquivos de questões devem seguir o modelo abaixo.

### Exemplo de Estrutura de um Arquivo de Questão (`.json`):

Cada arquivo `.json` contém uma lista principal chamada `"questions"`. Cada item nessa lista é um objeto que representa uma única questão, com a seguinte estrutura:

```json
{
  "questions": [
    {
      "type": "order_the_words",
      "instructions": "Order the words to make questions.",
      "example": "Example: work / do / you / where\nWhere do you work?",
      "qa_pairs": [
        {
          "item": "1 do / what / you / do",
          "answer": "What do you do?"
        },
        {
          "item": "2 a / uniform / a / does / nurse / wear",
          "answer": "Does a nurse wear a uniform?"
        }
      ]
    },
    {
      "type": "fill_in_the_blanks",
      "instructions": "Complete the sentences with the correct form of the verb in brackets.",
      "example": "It doesn’t rain (not rain) a lot in Egypt.",
      "qa_pairs": [
        {
          "item": "1 - I _______________ (watch TV) every evening.",
          "answer": "watch TV"
        }
      ]
    }
  ]
}
```

  * **`type`**: Um identificador para o tipo de exercício (útil para formatações futuras).
  * **`instructions`**: O enunciado principal.
  * **`example`**: O exemplo da questão, se houver.
  * **`qa_pairs`**: Uma lista de pares, onde cada objeto contém um `"item"` (a pergunta/sentença para o aluno) e seu correspondente `"answer"` (a resposta correta).

## 🤝 Como Contribuir

Contribuições para melhorar o projeto são muito bem-vindas\! Para manter a organização, o desenvolvimento e o rastreamento de mudanças, pedimos que todo o trabalho seja feito através do fluxo de Pull Requests do GitHub, seguindo estritamente os passos abaixo.

### Fluxo de Contribuição

1.  **Passo 1: Crie uma Branch**

      * A partir da branch `develop`, crie uma nova branch local para trabalhar na sua alteração.
      * Siga o padrão de nomenclatura definido na seção "Nomenclatura de Branches" (ex: `feature/add-new-filter`).

2.  **Passo 2: Crie um Pull Request (PR)**

      * Após finalizar suas alterações e fazer o push da sua branch, abra um novo Pull Request no repositório do GitHub.

      * No formulário do PR, preencha as seguintes informações no painel à direita:

        * **Assignees**: Atribua a você mesmo ou ao responsável pela revisão.
        * **Labels**: Adicione uma ou mais labels que classifiquem o PR (`bug`, `documentation`, `enhancement`, `etc`.).
        * **Projects**: Associe o PR ao projeto "CCB Quiz Generator".
        * **Milestone**: Vincule o PR ao marco de desenvolvimento relevante, como "**Functional Website**".

### Nomenclatura de branchs e commits
1. [Padrões de nomenclatura para commits](https://github.com/iuricode/padroes-de-commits/blob/main/README.md)
2. [Padrões de nomenclatura para branchs](https://medium.com/prolog-app/nossos-padr%C3%B5es-de-nomenclatura-para-branches-e-commits-fade8fd17106)