# Internetowe Kasyno

> **Motto projektu:** *„Dzisiaj w Betlejem, jutro Bentleyem”* 🚗💨  
> Platforma rozrywkowa online oferująca proste gry losowe i zręcznościowe dla pełnoletnich użytkowników.  
> Każdy znajdzie coś dla siebie — od klasycznej ruletki po dynamiczny coinflip!

---

<p align="center">
  <img src="./design/logo_prototype.jpeg" alt="kasyno logo" width="300">
</p>




## Opis projektu

**Internetowe Kasyno** to aplikacja webowa umożliwiająca użytkownikom grę w różne mini-gry oparte na losowości i zręczności.  
Celem projektu jest stworzenie bezpiecznego, intuicyjnego i atrakcyjnego środowiska do rozgrywki online z zachowaniem zasad fair play.

Projekt ma charakter **edukacyjny i demonstracyjny** – nie służy do prawdziwego hazardu.

---

## Zakres MVP (Minimum Viable Product)


### Rejestracja i logowanie
- Tworzenie nowego konta użytkownika  
- Logowanie z wykorzystaniem hasła (opcjonalnie 2FA)  
- Weryfikacja pełnoletności

### Zarządzanie kontem użytkownika
- Edycja danych profilu  
- Zmiana hasła  
- Podgląd historii gier i transakcji  

### Portfel i saldo użytkownika
- Wirtualna waluta (MufaCOIN)  
- Doładowanie i wypłata środków (symulacja)  
- Historia transakcji  

### Rozgrywka – proste gry
Dostępne mini-gry w wersji MVP:
- 🎲 **Ruletka** – klasyczna europejska ruletka z jednym zerem  
- 💣 **Saper** – gra logiczno-losowa z możliwością wygrania punktów  
- 🎰 **Slot** – automat z symbolami (trzy bębny, system nagród)  
- 🎯 **Suwak** – gra refleksu i precyzji  
- 🪙 **Coinflip** – rzut monetą: orzeł czy reszka?

### Bezpieczeństwo
- Szyfrowanie haseł
- Walidacja danych użytkownika  
- Sesje z tokenami JWT  

### System rankingowy
- Tabela najlepszych graczy (tygodnia?)
- Punkty rankingowe zależne od aktywności i wygranych  
- Odznaki i poziomy prestiżu  

---

## Technologia

| Warstwa | Technologia |
|----------|--------------|
| Frontend | Vue |
| Backend  | Node.js (Express) |
| Baza danych |  PostgreSQL |
| ORM | Prisma |
| Dokumentacja | Swagger UI |


---

# Backend

## Struktura projektu

### Główne katalogi
```
backend/
├── prisma                          # Konfiguracja i zarządzanie bazą danych
│   ├── prismaSingleton.ts          # Singleton klienta Prisma (pojedyncze połączenie DB)
│   ├── schema.prisma               # Definicje modeli, relacji i enumów
│   ├── seedRich.ts                 # Rozszerzone dane testowe (bogatszy seed)
│   └── seed.ts                     # Podstawowy seed bazy danych
└── src
    ├── Controllers                 # Logika biznesowa poszczególnych endpointów
    │   ├── admin.Controller.ts         # Operacje administracyjne (zarządzanie graczami, grami)
    │   ├── auth.Controller.ts          # Rejestracja, logowanie, autoryzacja
    │   ├── coinFlip.Controller.ts      # Logika gry CoinFlip
    │   ├── passwordReset.Controller.ts # Resetowanie haseł i obsługa tokenów
    │   ├── ranking.Controller.ts       # Generowanie rankingów graczy
    │   ├── roulette.Controller.ts      # Logika gry Ruletka
    │   ├── sapper.Controller.ts        # Logika gry Saper
    │   ├── slider.Controller.ts        # Logika gry Slider
    │   ├── slots.Controller.ts         # Logika gry Slot Machine
    │   └── wallet.Controller.ts        # Operacje portfela (wpłaty, wypłaty, saldo)
    ├── index.ts                     # Główny punkt startowy serwera Express
    ├── Middleware                   # Middleware zabezpieczeń i walidacji
    │   ├── admin.Middleware.ts         # Sprawdzanie uprawnień administratora
    │   ├── auth.Middleware.ts          # Weryfikacja tokenów JWT
    │   └── balance.Middleware.ts       # Sprawdzanie salda przed rozpoczęciem gry
    ├── Routes                       # Definicje tras API
    │   ├── admin.Routes.ts             # Trasy panelu administratora
    │   ├── games.Routes.ts             # Trasy wspólne dla gier
    │   ├── ranking.Routes.ts           # Trasy rankingów
    │   ├── sapper.Routes.ts            # Dedykowane trasy gry Saper
    │   ├── user.Routes.ts              # Trasy użytkownika (profil, auth)
    │   └── wallet.Routes.ts            # Trasy portfela użytkownika
    └── Services                     # Warstwa usług (logika pomocnicza)
        ├── special.file.ts             # Plik pomocniczy / narzędziowy (custom logic)
        └── wallet.Service.ts           # Logika biznesowa portfela (używana przez kontrolery)
```


## Struktura bazy danych

### Główne modele

#### User
Użytkownicy aplikacji z podstawowymi danymi osobowymi, rolą (NORMAL/ADMIN) i systemem banów.
- **Klucze:** email (unikalny), id (UUID)
- **Relacje:** 1:1 z Wallet, 1:N z SapperMap, 1:N z PasswordReset

#### Wallet  
Portfel użytkownika przechowujący saldo w formacie Decimal(10,2).
- **Relacje:** 1:1 z User, 1:N z Transaction

#### Transaction
Historia operacji finansowych (wpłaty, wypłaty, zakłady, wygrane).
- **Typy:** DEPOSIT, WITHDRAWAL, LOST, WIN, BET

#### SapperMap
Aktywna gra Saper użytkownika z planszą zapisaną jako string.
- **Ograniczenie:** jeden aktywny Saper na użytkownika

#### Game
Katalog dostępnych gier w kasynie z możliwością włączania/wyłączania.

#### PasswordReset
Tokeny resetowania hasła powiązane z użytkownikiem.
- **Indeksy:**  po userId oraz expiresAt

### Kluczowe cechy
- **UUID** jako ID we wszystkich tabelach
- **Cascade delete** dla powiązanych danych użytkownika (Wallet, Transaction, SapperMap, PasswordReset)
- **Indeksy** na często wyszukiwanych polach
- **Enumy** dla ról użytkowników (UserRole), typów transakcji (TransactionType) oraz typów gier (GameType)
- **Unikalność relacji 1:1** np. userId w Wallet i SapperMap

**Uwaga:** Tabela `spatial_ref_sys` to systemowa tabela PostgreSQL i nie jest częścią logiki aplikacji.

## Logika gier

### Mechanika i wypłaty

| Gra | RNG | Mechanika | Wypłaty | House Edge |
|-----|-----|-----------|---------|------------|
| **Ruletka** | `Math.random() * 100 % 37` | Liczby 0-36 + kolory (parz./nieparz.) | Liczba: 5x, Kolor: 2x (kumulatywne) | ~13.5% |
| **Coinflip** | `Math.random() * 100 % 2` | 50/50 (parz./nieparz.) | 2x przy wygranej | 0% |
| **Slots** | Weighted random | 9 symboli, 3 bębny, wypłaty za 2 i 3 symbole | 2 symbole: 0.5–10x, 3 symbole: 2–50x | Zmienny |
| **Slider** | `getRandomInt(0, 100)` | Gracz wybiera zakres [min,max] | `bet * (100/zakres) * 0.98` | 2% |
| **Saper** | - | NxN plansza, progresywny mnożnik | Rośnie z odkrytymi polami | Zmienny |

### Slot Machine - symbole i wagi
| Symbol | Waga | Wypłata (2x) | Wypłata (3x) | 
|--------|------|--------------|--------------|
| 🍒 CHERRY | 50 | 0.5x | 2x |
| 🍋 LEMON | 50 | 0.5x | 2x |
| 🍊 ORANGE | 45 | 1x | 3x |
| 🍇 PLUM | 50 | 1x | 4x |
| 🍇 GRAPE | 35 | 2x | 5x |
| 🍉 WATERMELON | 30 | 2x | 8x |
| 🔔 BELL | 25 | 3x | 10x |
| ⭐ STAR | 20 | 5x | 15x |
| 7️⃣ SEVEN | 15 | 10x | 50x |


### Zabezpieczenia
- **Walidacja:** Wszystkie kontrolery sprawdzają użytkownika
- **Transakcje:** Każda gra → wpis w `Transaction` (WIN/LOST)  
- **Atomowość:** Operacje Prisma w pojedynczych transakcjach
- **Error handling:** Pełne obsługa błędów z kodami HTTP

## Instrukcja uruchomienia
Aby poprawnie uruchomić serwer lokelnie, wykonaj poniższe kroki w głównym katalogu projektu.

### 1. Wymagania systemowe
- Node.js v16.0 lub nowszy
- npm v8.0 lub nowszy  
- PostgreSQL v12 lub nowszy

### 2. Instalacja zależności
    npm install

### 3. Konfiguracja zmiennych środowiskowych (.env)
Utwórz plik .env w głównym katalogu (tam gdzie package.json) i uzupełnij go według wzoru:

    DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DATABASE?schema=public"
    JWT_SECRET="twoj_tajny_klucz_jwt"
    PORT=8000

### 4. Baza danych (Prisma)
Synchronizacja schematu bazy danych (tworzenie tabel) oraz generowanie klienta Prisma.
**Uwaga:** Plik schematu znajduje się w folderze backend/prisma/

Wpisz następujące komendy do terminala:

  #### Generowanie klienta (wymagane przy pierwszym uruchomieniu)
    npx prisma generate --schema ./backend/prisma/schema.prisma

  #### Wypchnięcie zmian do bazy danych
    npx prisma db push --schema ./backend/prisma/schema.prisma

### 5.Uruchomienie serwera
Uruchom backend w trybie developerskim (z automatycznym restartem nodemon):

    npm run backend


## Dokumentacja API
Projekt posiada automatycznie generowaną dokumentację endpointów (Swagger).
Po uruchomieniu serwera wejdź na adres z dopiskiem `/docs` w adresie, np.:

http://localhost:8000/docs

### Opis endpointów

#### Roulette
- `POST /api/games/play-roulette` – Gra w ruletkę

#### Coin Flip
- `POST /api/games/play-coin-flip` – Gra w orzeł czy reszka

#### Slots
- `POST /api/games/play-slots` – Gra na automacie

#### Slider
- `POST /api/games/play-slider` – Gra na suwaku

#### Rankings
- `GET /api/ranking/{period}` – Ranking graczy (wg wygranych)

#### Sapper Game
- `POST /api/Sapper/start-sapper` – Rozpocznij nową grę Saper
- `POST /api/Sapper/play-sapper` – Wykonaj ruch w Saperze
- `POST /api/Sapper/resign-sapper` – Zakończ grę Saper

#### Users
- `GET /api/users/profile` – Pobierz profil użytkownika
- `POST /api/users/register` – Rejestracja
- `POST /api/users/login` – Logowanie
- `GET /api/users/is-authenticated` – Sprawdź autoryzację
- `PATCH /api/users/update-username` – Zmień nazwę użytkownika
- `PATCH /api/users/update-update-email` – Zmień adres e-mail
- `PATCH /api/users/update-changePassword` – Zmień hasło
- `PATCH /api/users/update-delete-user` – Usuń konto

#### Wallet
- `GET /api/wallet/get-wallet` – Pobierz portfel
- `POST /api/wallet/deposit` – Dodaj środki do portfela
- `POST /api/wallet/withdraw` – Wypłać środki z portfela

#### Admin
- `GET /api/admin/list-users` – Lista użytkowników z paginacją i filtrowaniem
- `GET /api/admin/user-details/{id}` – Szczegóły użytkownika
- `PATCH /api/admin/patch-user/{id}` – Edycja danych użytkownika
- `DELETE /api/admin/delete-user/{id}` - Usunięcie użytkownika (tylko admin)

#### General
- `GET /` – Endpoint powitalny

## Bezpieczeństwo

### Autoryzacja JWT
- Tokeny są generowane przy logowaniu
- Middleware `authMiddleware.js` weryfikuje tokeny
- Tokeny zawierają ID użytkownika i czas wygaśnięcia

### Walidacja danych
- Dane wejściowe są walidowane ręcznie w kontrolerach 
- Walidacja wieku przy rejestracji
- Sprawdzanie unikalności emaila
- Walidacja haseł przy zmianie

### Hashowanie haseł
- Hasła są hashowane za pomocą bcrypt
- Salt rounds: 10 (domyślnie)

---

# Frontend

## Architektura aplikacji

Frontend zbudowany w **Vue 3** z **Composition API**, wykorzystujący nowoczesne narzędzia i biblioteki dla optymalnego user experience.


## Struktura projektu

### Główne katalogi
```
frontend/src/
├── assets/               # Statyczne zasoby (grafiki, style)
├── components/           # Komponenty wielokrotnego użytku
│   ├── games/            # Modale gier (Slots, Roulette, Slider, Minesweeper)
│   ├── layout/           # Layout aplikacji (Header, Footer)
│   ├── modals/           # Modale systemowe (Login, Register, Wallet, Admin)
│   ├── sections/         # Sekcje strony (Hero, GamesGrid, Leaderboard)
│   └── ui/               # Komponenty UI (GameCard, LeaderboardRow)
├── views/                # Widoki główne aplikacji
│   ├── HomeView.vue
│   ├── NotFoundView.vue
│   ├── ResetPasswordView.vue
│   └── user/             # Panel użytkownika
│       ├── UserDashboard.vue
│       ├── Profile.vue
│       ├── ChangePassword.vue
│       ├── PanelSectionLayout.vue
│       └── AccountSidebar.vue
├── router/               # Konfiguracja routingu (Vue Router)
├── stores/               # Magazyny stanu (Pinia)
├── main.js               # Punkt wejścia aplikacji
└── env.d.ts              # Typowanie zmiennych środowiskowych
```

### Routing i nawigacja
System routingu obsługuje:
- **Publiczne trasy** (`/home`, `/games`, `/leaderboard`)
- **Chronione trasy** (`/panel/*` - wymaga autoryzacji)
- **Trasy administracyjne** (`/admin` - tylko dla adminów)
- **Strony pomocnicze** (`/legal/*`, `/support/*`)

### State Management

#### Auth Store
Centralny magazyn autoryzacji obsługujący:
- **Autentyfikację JWT** - logowanie i wylogowanie użytkownika
- **Dane użytkownika** - profil, rola, uprawnienia
- **Saldo portfela** - aktualne środki oraz historia transakcji
- **Persystencję** - zapis tokena i danych użytkownika w `localStorage`

```typescript
// Kluczowe metody auth store
loginSuccess(token, user) // Logowanie użytkownika i zapis danych 
fetchBalance() // Pobieranie salda i transakcji z API 
updateUsername(newUsername) // Aktualizacja nazwy użytkownika 
logout() // Wylogowanie i czyszczenie danych
```

## Komponenty gier

### Modale gier
Każda gra ma dedykowany modal z ujednoliconą strukturą:
- 🎰 **SlotGameModal** - automat z 3 bębnami i 9 symbolami
- 🎲 **RouletteGameModal** - ruletka europejska 0-36
- 🪙 **CoinflipGameModal** - rzut monetą z animacjami
- 🎯 **SliderGameModal** - gra precyzyjna z suwakiem
- 💣 **MinesweeperGameModal** - saper z progresywnym mnożnikiem

### Wspólne cechy modali gier:
- **Walidacja zakładów** - sprawdzanie salda przed grą
- **Animacje rezultatów** - confetti przy wygranych
- **Real-time updates** - natychmiastowa aktualizacja salda
- **Error handling** - obsługa błędów API i sieci

## Interfejs użytkownika

### Design System
- **Motyw** - ciemny z gradientowymi akcentami (fiolet/cyan)
- **Typografia** - Space Grotesk (Google Fonts)
- **Ikony** - Material Symbols Outlined
- **Kolory** - gradientowe tła, transparentne elementy
- **Responsywność** - mobile-first, adaptacyjny layout

### Komponenty UI
- **GameCard** - karty gier z hover effects
- **GameGrid** - siatka prezentująca dostępne gry.
- **LeaderboardSection** - sekcja rankingu z tabelą HTML, dynamicznym kolorowaniem TOP 3 (złoty/srebrny/brązowy) i filtrowaniem okresów (All/Month/Week).
- **HeroSection** - baner powitalny z dynamicznym tłem i przyciskiem Call-to-Action.
- **HeaderComponent** - różne wersje dla auth/unauth
- **FooterComponent** - linki prawne i wsparcie

### Animacje i UX
- **Backdrop blur** - rozmycie tła pod modalami i elementami interfejsu
- **Hover states** - interaktywne stany przycisków i kart
- **Loading states** - wskaźniki ładowania
- **Canvas confetti** - fajerwerki przy wygranych

## Panel użytkownika

Chroniona sekcja `/panel` z podstronami:
- **Dashboard** - podsumowanie konta i aktywności
- **Profil** - edycja danych osobowych
- **Hasło** - zmiana hasła

## Zabezpieczenia frontend

### Ochrona tras
- **Route guards** - middleware sprawdzający autoryzację
- **Role-based access** - różne uprawnienia (USER/ADMIN)
- **Token validation** - weryfikacja JWT w każdym żądaniu

### Walidacja po stronie klienta
- **Input validation** - sprawdzanie formularzy przed wysłaniem
- **XSS protection** - ochrona przed atakami skryptowymi
- **CSRF tokens** - (planowane) tokeny antyfałszywościowe

## Instrukcja uruchomienia Frontend

### 1. Wymagania systemowe
- Node.js v20.19+ lub v22.12+
- npm v8.0 lub nowszy
- Nowoczesna przeglądarka (Chrome 90+, Firefox 88+)

### 2. Instalacja zależności
```bash
cd frontend
npm install
```

### 3. Uruchomienie w trybie deweloperskim
```bash
npm run dev
```

### 4. Build produkcyjny
```bash
npm run build      # Budowanie
npm run preview    # Podgląd buildu
```


# Uruchomienie z Docker (Zalecane)

Możesz uruchomić całą aplikację za pomocą jednej komendy, bez konieczności lokalnej instalacji Node.js czy PostgreSQL.

## 1. Wymagania
- Docker Desktop (lub Docker Engine + Docker Compose)

## 2. Konfiguracja
Upewnij się, że w głównym katalogu projektu znajduje się plik `.env` skonfigurowany zgodnie z sekcją Backend.
Dla Dockera `DB_HOST` w pliku .env powinien być ustawiony na nazwę usługi bazy danych (zazwyczaj `db` lub `postgres`), a nie `localhost`.

## 3. Uruchomienie
W głównym katalogu projektu wykonaj komendę:

```bash
docker-compose up --build
```

Aby zatrzymać aplikację:

```bash
docker-compose down
```
