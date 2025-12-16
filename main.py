import json


# --- 1. Trieda pre Aktivitu (Activity) ---
class Activity:
    def __init__(self, id, name, duration, predecessors=None):
        self.id = id
        self.name = name
        self.duration = duration
        # Ak nemá predchodcov, vytvoríme prázdny zoznam
        self.predecessors = predecessors if predecessors else []
        self.successors = []  # Doplníme automaticky pri stavbe siete

        # Vypočítané hodnoty (Early Start/Finish, Late Start/Finish)
        self.ES = 0  # Najskorší začiatok
        self.EF = 0  # Najskorší koniec
        self.LS = float('inf')  # Najneskorší začiatok
        self.LF = float('inf')  # Najneskorší koniec
        self.is_critical = False  # Príznak kritickej cesty

    def __repr__(self):
        return f"[{self.id}] {self.name} (Trvanie: {self.duration})"


# --- 2. Trieda pre Sieť (Network) ---
class Network:
    def __init__(self):
        self.activities = {}  # Slovník: id -> objekt Activity

    def add_activity(self, activity):
        self.activities[activity.id] = activity

    def calculate_cpm(self):
        """Hlavná metóda spúšťajúca algoritmy CPM."""
        ids = list(self.activities.keys())

        # --- A. Dopredný priechod (Forward Pass) ---
        # Pravidlo: ES = max(EF predchodcov), EF = ES + trvanie
        for aid in ids:
            act = self.activities[aid]
            if not act.predecessors:
                # Ak nemá predchodcu, začína v čase 0
                act.ES = 0
            else:
                # Nájdeme maximálny EF zo všetkých predchodcov
                max_prev_ef = 0
                for pred_id in act.predecessors:
                    if pred_id in self.activities:
                        max_prev_ef = max(max_prev_ef, self.activities[pred_id].EF)
                act.ES = max_prev_ef

            # Výpočet skorého konca
            act.EF = act.ES + act.duration

        # --- B. Spätný priechod (Backward Pass) ---
        # Najprv zistíme dĺžku celého projektu (max EF zo všetkých)
        project_duration = max(a.EF for a in self.activities.values())

        # Prechádzame poľom odzadu
        for aid in reversed(ids):
            act = self.activities[aid]

            # Ak nemá nasledovníkov, jeho LF je koniec projektu
            if not act.successors:
                act.LF = project_duration
            else:
                # Nájdeme minimálny LS zo všetkých nasledovníkov
                min_next_ls = float('inf')
                for succ_id in act.successors:
                    if succ_id in self.activities:
                        min_next_ls = min(min_next_ls, self.activities[succ_id].LS)
                act.LF = min_next_ls

            # Výpočet neskorého začiatku
            act.LS = act.LF - act.duration

            # Určenie kritickej cesty (ak je rezerva 0)
            # Rezerva (Float) = LS - ES
            if (act.LS - act.ES) == 0:
                act.is_critical = True

    def print_results(self):
        """Výpis výsledkov do tabuľky."""
        print(f"{'ID':<5} {'Názov':<20} {'Trv':<5} {'ES':<5} {'EF':<5} {'LS':<5} {'LF':<5} {'Kritická?'}")
        print("-" * 75)
        for act in self.activities.values():
            crit = "*" if act.is_critical else ""
            print(
                f"{act.id:<5} {act.name:<20} {act.duration:<5} {act.ES:<5} {act.EF:<5} {act.LS:<5} {act.LF:<5} {crit}")


# --- 3. Návrhový vzor Builder ---
class NetworkBuilder:
    def __init__(self):
        self._network = Network()

    def load_from_json(self, filepath):
        """Načíta dáta zo súboru a ošetrí chyby (Try/Except)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validácia: dáta musia byť zoznam
            if not isinstance(data, list):
                raise ValueError("JSON musí obsahovať zoznam aktivít.")

            # 1. Krok: Vytvorenie objektov aktivít
            for item in data:
                # Ošetrenie chýbajúcich kľúčov
                if 'id' not in item or 'duration' not in item:
                    print(f"Varovanie: Preskakujem neplatný záznam: {item}")
                    continue

                act = Activity(
                    id=item['id'],
                    name=item.get('name', 'Nepomenovaná'),
                    duration=item['duration'],
                    predecessors=item.get('predecessors', [])
                )
                self._network.add_activity(act)

            # 2. Krok: Prepojenie nasledovníkov (Successors) pre spätný priechod
            # Prechádzame aktivity a 'oznámime' predchodcom, kto je ich nasledovník
            for act in self._network.activities.values():
                for pred_id in act.predecessors:
                    if pred_id in self._network.activities:
                        self._network.activities[pred_id].successors.append(act.id)

            return True

        except FileNotFoundError:
            print("CHYBA: Súbor nebol nájdený. Skontrolujte názov 'data.json'.")
            return False
        except json.JSONDecodeError:
            print("CHYBA: Súbor nie je validný JSON (chyba syntaxe).")
            return False
        except Exception as e:
            print(f"CHYBA: Nastala neočakávaná chyba: {e}")
            return False

    def get_network(self):
        return self._network


# --- 4. Hlavné spustenie (Main) ---
if __name__ == "__main__":
    # Vytvorenie inštancie Buildera
    builder = NetworkBuilder()

    # Načítanie dát
    if builder.load_from_json("data.json"):
        print("Dáta úspešne načítané. Spúšťam výpočet CPM...\n")

        # Získanie siete a výpočet
        network = builder.get_network()
        network.calculate_cpm()

        # Výpis
        network.print_results()