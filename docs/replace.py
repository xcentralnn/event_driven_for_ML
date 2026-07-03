import os
import glob
for f in glob.glob('chapters/*.tex'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('\\subsection{', '\\subsubsection{')
    content = content.replace('\\section{', '\\subsection{')
    content = content.replace('\\chapter{', '\\section{')
    content = content.replace('\\chapter*{', '\\section*{')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
