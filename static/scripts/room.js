document.addEventListener('DOMContentLoaded', () => {
   const socket = io();
   const codeArea = document.getElementById('codeArea');
   const lineNumbers = document.getElementById('lineNumbers');
   const copyCodeButton = document.getElementById('copyCodeButton');
   const noInternetOverlay = document.getElementById('noInternetOverlay');

   noInternetOverlay.addEventListener('dblclick', () => {
       noInternetOverlay.style.display = 'none';
   });

   const updateLineNumbers = () => {
       const lineCount = codeArea.value.split('\n').length;
       lineNumbers.innerHTML = Array.from({ length: lineCount }, (_, i) => i + 1).join('<br>');
   };

   const updateCodeAreaContent = () => {
       hljs.highlightElement(codeArea);
   };

   codeArea.addEventListener('scroll', () => {
       lineNumbers.scrollTop = codeArea.scrollTop;
   });

   socket.emit('join');

   socket.on('code_update', (data) => {
       codeArea.value = data;
       updateLineNumbers();
       updateCodeAreaContent();
   });

   codeArea.addEventListener('input', () => {
       socket.emit('code_update', codeArea.value);
       updateLineNumbers();
       updateCodeAreaContent();
   });

   codeArea.addEventListener('keydown', (e) => {
       if (e.key === 'Tab') {
           e.preventDefault();
           const start = codeArea.selectionStart;
           const end = codeArea.selectionEnd;
           codeArea.value = codeArea.value.substring(0, start) + '    ' + codeArea.value.substring(end);
           codeArea.selectionStart = codeArea.selectionEnd = start + 4;
           updateLineNumbers();
       }
   });

   copyCodeButton.addEventListener('click', () => {
       codeArea.select();
       document.execCommand('copy');

       copyCodeButton.innerHTML = '<i class="fas fa-check"></i>';
       setTimeout(() => {
           copyCodeButton.innerHTML = '<i class="fas fa-copy"></i> Copy Code';
       }, 2000);
   });

   updateLineNumbers();
   window.addEventListener('resize', updateLineNumbers);
   window.addEventListener('beforeunload', () => {
       socket.emit('leave');
   });

   updateCodeAreaContent();
});