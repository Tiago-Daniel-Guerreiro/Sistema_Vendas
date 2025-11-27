Vou enviar blocos de código, provavelmente ficheiro por ficheiro.
Deves analisar, verificar se a logica está implementada e correta, sugerir melhorias ou correções se necessário, verificar se segue os pontos abaixo, e devolver o bloco de código completo e corrigido.
Pontos a verificar:
1. Nomes em português e abreviados: Seja em variáveis, funções, classes, métodos, ficheiros, etc. Evitar nomes em inglês ou abreviados.
2. Comentários em português: Todos os comentários devem estar em português, explicando o propósito do código. Não deve aparecer código sobre uma explicação obvia mas em situações complexas deve haver comentários explicativos como na ligação de sockets deve haver uma explicação por exemplo a explicar o que está a ser usado para ter uma ligação TCP o que é e porquê.
3. Estrutura e organização: O código deve estar bem estruturado e organizado, com uma separação clara de responsabilidades. Funções e classes devem ter um único propósito bem definido.
4. Modularidade: O código deve ser modular, permitindo a reutilização de componentes e facilitando a manutenção. Por exemplo a lógica do servidor está em entities.py enquanto o server.py apenas chama e trata da parte do servidor.
5. Tratamento de erros: Deve haver um tratamento adequado de erros e exceções para garantir que o programa lida graciosamente com situações inesperadas.
6. Clean Code: O código deve seguir os princípios de Clean Code, incluindo nomes significativos, funções pequenas e coesas, e evitar duplicação de código.
7. Simplicidade: O código deve ser simples, evitando complexidade desnecessária pois há pouco tempo de desenvolvimento disponível, mas não deve remover complexidade existente só porque sim.
8. Código explícito: Nunca usar métodos complexos como filter, map e any, e sempre evitar if, else e for na mesma linha, tendo sempre em múltiplas linhas para melhor legibilidade.
9. Verificações explícitas: Evitar verificações implícitas ou confusas, por exemplo ao invés de if variavel: usar if variavel is not None: ou if len(variavel) > 0: conforme o caso.
10. Centralização de lógica: A lógica principal deve estar centralizada em locais apropriados, evitando dispersão pelo código.
11. Match: Deves usar match sempre ao invés de multiplos if else if
12. Módulos relacionados: Usar sempre a lógica dos módulos relacionados ao invés de estar a repetir (por exemplo ao invés de ter um método de limpar no cliente e no servidor é melhor usar o console.py que tem essa lógica)
13. Alterações desnecessárias: Deves evitar alterações desnecessárias quando não se está a incomprir diretamente algum ponto, mas podes fazer perguntas se não tiveres a certeza. Nunca usar """ """ para comentários e poucas vezes #, sendo que nunca deves comentar um método como """ Descrição """
14. Perguntas: Se tiveres dúvidas sobre o que fazer, deves perguntar antes de fazeres qualquer alteração.
15. Aviso: A qualquer momento podes/deves pedir para atualizar um ficheiro anterior, SEMPRE que necessário

