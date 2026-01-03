import json


# --- 1. Trieda pre Aktivitu (Activity) - "Múdrejšia" verzia ---
class Activity:
    def __init__(self, id, name, duration, predecessors=None):
        self.id = id
        self.name = name
        self.duration = duration
        self.predecessors = predecessors if predecessors else []
        self.successors = []

        # Hodnoty pre CPM
        self.ES = 0
        self.EF = 0
        self.LS = float('inf')
        self.LF = float('inf')
        self.is_critical = False

    def __repr__(self):
        return f"[{self.id}] {self.name} (Trv: {self.duration})"

    # --- Nové metódy pre zapuzdrenie výpočtov (podľa rady učiteľa) ---

    def calculate_early(self, max_predecessor_ef):
        """Vypočíta ES a EF na základe predchodcov."""
        self.ES = max_predecessor_ef
        self.EF = self.ES + self.duration

        # Jednoduchá kontrola (sanity check)
        if self.EF < self.ES:
            raise ValueError(f"Chyba v aktivite {self.id}: EF nemôže byť menšie ako ES.")

    def calculate_late(self, min_successor_ls, project_deadline=None):
        """Vypočíta LF a LS. Ak nemá nasledovníkov, použije deadline projektu."""
        if not self.successors and project_deadline is not None:
            self.LF = project_deadline
        else:
            self.LF = min_successor_ls

        self.LS = self.LF - self.duration

        # Kontrola, či LS nie je záporné (teoreticky možné len pri chybnom zadaní)
        if self.LS < 0:
            print(f"Varovanie: Aktivita {self.id} má záporný LS ({self.LS}). Skontrolujte väzby.")

    def calculate_float(self):
        """Vypočíta rezervu a určí, či je kritická."""
        total_float = self.LS - self.ES
        # Zaokrúhlenie kvôli desatinným chybám (float precision)
        if round(total_float, 2) == 0:
            self.is_critical = True
        else:
            self.is_critical = False
        return total_float


# --- 2. Trieda pre Sieť (Network) ---
class Network:
    def __init__(self):
        self.activities = {}  # id -> Activity

    def add_activity_object(self, activity):
        self.activities[activity.id] = activity

    def get_all_activities(self):
        return self.activities.values()

    def calculate_cpm(self):
        """Riadi algoritmus dopredného a spätného priechodu."""
        ids = list(self.activities.keys())

        # --- A. Dopredný priechod (Forward Pass) ---
        for aid in ids:
            act = self.activities[aid]

            # Zistíme max EF predchodcov
            max_prev_ef = 0
            if act.predecessors:
                # Využívame list comprehension pre čistotu kódu
                predecessor_efs = [
                    self.activities[p_id].EF
                    for p_id in act.predecessors
                    if p_id in self.activities
                ]
                if predecessor_efs:
                    max_prev_ef = max(predecessor_efs)

            # Necháme aktivitu, nech si vypočíta svoje časy (zapuzdrenie)
            act.calculate_early(max_prev_ef)

        # --- B. Spätný priechod (Backward Pass) ---
        project_duration = max(a.EF for a in self.activities.values())

        for aid in reversed(ids):
            act = self.activities[aid]

            # Zistíme min LS nasledovníkov
            min_next_ls = float('inf')

            # Ak má nasledovníkov, nájdeme minimum
            if act.successors:
                successor_ls_values = [
                    self.activities[s_id].LS
                    for s_id in act.successors
                    if s_id in self.activities
                ]
                if successor_ls_values:
                    min_next_ls = min(successor_ls_values)

            # Necháme aktivitu vypočítať si LS a LF
            act.calculate_late(min_next_ls, project_deadline=project_duration)

            # Výpočet rezervy
            act.calculate_float()

    def print_results(self):
        print(f"{'ID':<5} {'Názov':<20} {'Trv':<5} {'ES':<5} {'EF':<5} {'LS':<5} {'LF':<5} {'Kritická?'}")
        print("-" * 75)
        for act in self.activities.values():
            crit = "*" if act.is_critical else ""
            print(
                f"{act.id:<5} {act.name:<20} {act.duration:<5} {act.ES:<5} {act.EF:<5} {act.LS:<5} {act.LF:<5} {crit}")


# --- 3. Vylepšený Builder (Fluent Interface) ---
class NetworkBuilder:
    def __init__(self):
        self._network = Network()
        self._temp_data = []  # Dočasné úložisko pre JSON dáta

    def add_activity(self, id, name, duration, predecessors=None):
        """Pridá aktivitu do siete. Vracia self pre reťazenie (Fluent Interface)."""
        act = Activity(id, name, duration, predecessors)
        self._network.add_activity_object(act)
        return self  # <-- Toto chcel učiteľ (vracia staviteľa späť)

    def load_from_json(self, filepath):
        """Načíta JSON, ale zatiaľ len uloží dáta. Stavba prebehne až pri build()."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("JSON musí byť zoznam.")

            self._temp_data = data
            return self  # Opäť vraciame self

        except Exception as e:
            print(f"CHYBA pri čítaní JSON: {e}")
            self._temp_data = []
            return self

    def _link_successors(self):
        """Pomocná metóda na prepojenie nasledovníkov (interná logika)."""
        for act in self._network.activities.values():
            for pred_id in act.predecessors:
                if pred_id in self._network.activities:
                    self._network.activities[pred_id].successors.append(act.id)

    def build(self):
        """
        Finálna metóda:
        1. Spracuje načítané dáta (ak sú).
        2. Prepojí vzťahy (successors).
        3. Môže automaticky spustiť výpočet CPM.
        4. Vráti hotovú sieť.
        """
        # Spracovanie dát z JSONu (ak sme použili load_from_json)
        for item in self._temp_data:
            if 'id' in item and 'duration' in item:
                self.add_activity(
                    item['id'],
                    item.get('name', 'N/A'),
                    item['duration'],
                    item.get('predecessors', [])
                )

        # Prepojenie grafu
        self._link_successors()

        # Učiteľov tip: Builder môže rovno aktualizovať sieť o výpočty
        # Takže tu môžeme zavolať calculate_cpm(), aby užívateľ dostal hotovú vec.
        if self._network.activities:
            self._network.calculate_cpm()

        return self._network


# --- 4. Hlavné spustenie ---
if __name__ == "__main__":
    # Použitie vylepšeného Buildera
    # Všimni si, ako môžeme metódy reťaziť (aj keď tu voláme load a build oddelene pre prehľadnosť)

    builder = NetworkBuilder()

    # "Fluent" zápis by mohol vyzerať aj takto:
    # network = builder.load_from_json("data.json").build()

    # Klasický zápis:
    builder.load_from_json("data.json")
    network = builder.build()

    if network.activities:
        print("Sieť úspešne postavená a vypočítaná.\n")
        network.print_results()
    else:
        print("Nepodarilo sa vytvoriť sieť (chyba v dátach alebo prázdny súbor).")