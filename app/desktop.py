import json
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "http://127.0.0.1:8000"
COLORS = {
    "canvas": "#FFF7FB",
    "surface": "#FFFCFE",
    "border": "#EBD7E5",
    "ink": "#42283F",
    "muted": "#806C7D",
    "pink": "#D95798",
    "pink_hover": "#BE3F80",
    "violet": "#7652C8",
    "violet_hover": "#6040AC",
    "lavender": "#F2ECFF",
}


def api_request(path: str, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{API_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class LoanApplicationWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Loan Application Training Demo")
        self.root.geometry("600x490")
        self.root.configure(background=COLORS["canvas"])
        self._configure_styles()
        self.application_id: int | None = None
        self.customers: dict[str, int] = {}

        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Mock loan application", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16)
        )

        self.customer = tk.StringVar()
        self.loan_type = tk.StringVar(value="personal")
        self.amount = tk.StringVar(value="12000")
        self.term = tk.StringVar(value="36")
        self.purpose = tk.StringVar(value="Home repairs")
        self.status = tk.StringVar(value="Loading fictional customers...")

        self._field(frame, "Customer", ttk.Combobox(frame, textvariable=self.customer, state="readonly"), 1)
        self._field(
            frame,
            "Loan type",
            ttk.Combobox(
                frame,
                textvariable=self.loan_type,
                values=("personal", "auto", "home", "business"),
                state="readonly",
            ),
            2,
        )
        self._field(frame, "Amount ($)", ttk.Entry(frame, textvariable=self.amount), 3)
        self._field(frame, "Term (months)", ttk.Entry(frame, textvariable=self.term), 4)
        self._field(frame, "Purpose", ttk.Entry(frame, textvariable=self.purpose), 5)

        self.create_button = ttk.Button(
            frame, text="Create draft", style="Pink.TButton", command=self.create_draft
        )
        self.create_button.grid(row=6, column=0, sticky="w", pady=(20, 8))
        self.confirm_button = ttk.Button(
            frame,
            text="Confirm mock submission",
            style="Violet.TButton",
            command=self.confirm_submission,
            state="disabled",
        )
        self.confirm_button.grid(row=6, column=1, sticky="e", pady=(20, 8))
        ttk.Label(frame, textvariable=self.status, style="Status.TLabel", wraplength=520).grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        frame.columnconfigure(1, weight=1)
        self.customer_widget = frame.grid_slaves(row=1, column=1)[0]
        self.load_customers()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["canvas"])
        style.configure(
            "TLabel",
            background=COLORS["canvas"],
            foreground=COLORS["ink"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            foreground=COLORS["violet"],
            font=("Segoe UI", 19, "bold"),
        )
        style.configure(
            "Status.TLabel",
            foreground=COLORS["muted"],
            background=COLORS["lavender"],
            padding=(10, 8),
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["ink"],
            insertcolor=COLORS["violet"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=8,
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", COLORS["violet"])],
            lightcolor=[("focus", COLORS["violet"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["surface"],
            background=COLORS["lavender"],
            foreground=COLORS["ink"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            arrowcolor=COLORS["violet"],
            padding=8,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["surface"])],
            bordercolor=[("focus", COLORS["violet"])],
            lightcolor=[("focus", COLORS["violet"])],
        )
        for name, color, hover in (
            ("Pink.TButton", COLORS["pink"], COLORS["pink_hover"]),
            ("Violet.TButton", COLORS["violet"], COLORS["violet_hover"]),
        ):
            style.configure(
                name,
                background=color,
                foreground="#FFFFFF",
                font=("Segoe UI", 10, "bold"),
                padding=(12, 9),
                borderwidth=0,
            )
            style.map(
                name,
                background=[("disabled", COLORS["border"]), ("active", hover)],
                foreground=[("disabled", COLORS["muted"])],
            )

    @staticmethod
    def _field(frame: ttk.Frame, label: str, widget: tk.Widget, row: int) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6)
        widget.grid(row=row, column=1, sticky="ew", pady=6)

    def load_customers(self) -> None:
        try:
            customers = api_request("/customers")
            self.customers = {f"{row['name']} (ID {row['id']})": row["id"] for row in customers}
            self.customer_widget.configure(values=list(self.customers))
            if self.customers:
                self.customer.set(next(iter(self.customers)))
            self.status.set("Connected to local mock API. No real bank is contacted.")
        except (HTTPError, URLError, TimeoutError) as error:
            self.status.set(f"API unavailable. Start the API first: {error}")

    def create_draft(self) -> None:
        try:
            payload = {
                "customer_id": self.customers[self.customer.get()],
                "loan_type": self.loan_type.get(),
                "amount": float(self.amount.get()),
                "term_months": int(self.term.get()),
                "purpose": self.purpose.get(),
            }
            application = api_request("/applications", "POST", payload)
            self.application_id = application["id"]
            self.confirm_button.configure(state="normal")
            self.status.set(
                f"Draft #{self.application_id} created for {application['customer_name']}. "
                "It has not been submitted."
            )
        except (KeyError, ValueError, HTTPError, URLError, TimeoutError) as error:
            self.status.set(f"Could not create draft: {error}")

    def confirm_submission(self) -> None:
        if self.application_id is None:
            return
        confirmed = messagebox.askyesno(
            "Confirm mock submission",
            f"Submit draft #{self.application_id} to the local mock database?\n\n"
            "This does not contact a real bank.",
            parent=self.root,
        )
        if not confirmed:
            return
        try:
            application = api_request(
                f"/applications/{self.application_id}/submit",
                "POST",
                {"confirmation": True},
            )
            self.confirm_button.configure(state="disabled")
            self.status.set(f"Mock application #{application['id']} submitted.")
        except (HTTPError, URLError, TimeoutError) as error:
            self.status.set(f"Could not submit mock application: {error}")


def main() -> None:
    root = tk.Tk()
    LoanApplicationWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
