document.addEventListener('DOMContentLoaded', () => {
   const socket = io();
   const codeArea = document.getElementById('codeArea');
   const lineNumbers = document.getElementById('lineNumbers');
   const copyCodeButton = document.getElementById('copyCodeButton');
   const suggestCodeButton = document.getElementById('suggestCodeButton');
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

   suggestCodeButton.addEventListener('click', () => {
       fetch('https://cf.api.altacee.com/get_code', {
           method: 'POST',
           headers: {
               'Content-Type': 'application/json'
           },
           body: JSON.stringify({ prompt: codeArea.value })
       })
       .then(response => response.json())
       .then(data => {
           if (data.success) {
               let suggestedCode = data.result.response;

               // Check if the response contains code block markers (```)
               if (suggestedCode.includes('```')) {
                   // Remove the markdown code block formatting if present
                   suggestedCode = suggestedCode.replace(/```[a-z]*\n|\n```/g, '');
               }

               // Update the code area with the suggested code
               codeArea.value = suggestedCode;
               updateLineNumbers();
               updateCodeAreaContent();

               // Emit the updated code to all connected clients
               socket.emit('code_update', suggestedCode);
           } else {
               console.error('Failed to get code suggestions:', data.errors);
           }
       })
       .catch(error => {
           console.error('Error fetching code suggestions:', error);
       });
   });

   updateLineNumbers();
   window.addEventListener('resize', updateLineNumbers);
   window.addEventListener('beforeunload', () => {
       socket.emit('leave');
   });

   updateCodeAreaContent();
});
