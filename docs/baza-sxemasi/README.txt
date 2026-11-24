Ma'lumotlar bazasi sxemasi (ER diagramma): barcha Django modellari va bog'lanishlari.
*.mmd — Mermaid manba, *.svg — tayyor rasm (overview — umumiy, qolganlari — ilovalar bo'yicha).
Yangilash: python3 -I 1_parse.py ../../backend models.json; python3 -I 2_gen.py models.json out; so'ng `mmdc -i fayl.mmd -o fayl.svg`.
overview.mmd qo'lda yig'ilgan (bo'limlar bloki); model qo'shilsa uni ham yangilang.
