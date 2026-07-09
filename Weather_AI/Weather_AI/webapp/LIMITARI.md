# Limitări aplicație Weather AI

1. Aplicația permite doar interogări de tip SELECT.
   Interogările INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE, GRANT și REVOKE sunt blocate.

2. Validarea SQL este realizată prin verificarea unor cuvinte cheie interzise.
   Această metodă oferă protecție de bază, dar nu înlocuiește complet un sistem avansat de securitate SQL.

3. Aplicația folosește un model LLM pentru generarea interogărilor SQL și pentru sumarizarea rezultatelor.
   Din acest motiv pot exista costuri și latență la fiecare interogare.

4. Rezultatele depind de datele existente în baza de date MySQL.
   Aplicația nu oferă prognoză meteo în timp real, ci interoghează datele deja importate din fișiere CSV.

5. Pentru siguranță, în producție este recomandată folosirea unui utilizator MySQL cu drepturi limitate.
   Ideal, utilizatorul trebuie să aibă SELECT pe datele meteo și INSERT doar pe tabela chat_history.

6. Întrebările fără legătură cu domeniul meteo sunt clasificate separat și nu sunt transformate în SQL.