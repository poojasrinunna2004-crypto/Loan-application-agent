import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = os.environ.get("LOAN_AGENT_API_URL", "http://127.0.0.1:8000").rstrip("/")
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
    "error": "#9E3D67",
    "error_surface": "#FDEEF5",
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
        self.root.geometry("660x690")
        self.root.minsize(600, 650)
        self.root.configure(background=COLORS["canvas"])
        self._configure_styles()
        self.application_id: int | None = None
        self.customers: dict[str, int] = {}

        frame = ttk.Frame(root, padding=26)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Loan application", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            frame,
            text="Prepare a sample application and review it before submission.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(3, 16))

        self.status = tk.StringVar(value="Connecting to the mock service...")
        self.status_label = ttk.Label(
            frame, textvariable=self.status, style="Status.TLabel", wraplength=500
        )
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.retry_button = ttk.Button(
            frame, text="Retry", style="Quiet.TButton", command=self.load_customers
        )
        self.retry_button.grid(row=2, column=2, sticky="e", padx=(10, 0), pady=(0, 14))

        form = ttk.LabelFrame(
            frame, text="Application details", style="Section.TLabelframe", padding=(16, 10)
        )
        form.grid(row=3, column=0, columnspan=3, sticky="ew")
        form.columnconfigure(1, weight=1)
        self.customer = tk.StringVar()
        self.loan_type = tk.StringVar(value="Personal")
        self.amount = tk.StringVar()
        self.term = tk.StringVar(value="36")
        self.purpose = tk.StringVar()

        self.customer_widget = ttk.Combobox(
            form, textvariable=self.customer, state="disabled"
        )
        self.loan_type_widget = ttk.Combobox(
            form,
            textvariable=self.loan_type,
            values=("Personal", "Auto", "Home", "Business"),
            state="readonly",
        )
        self.amount_widget = ttk.Entry(form, textvariable=self.amount)
        self.term_widget = ttk.Entry(form, textvariable=self.term)
        self.purpose_widget = ttk.Entry(form, textvariable=self.purpose)
        self.form_widgets = (
            self.customer_widget,
            self.loan_type_widget,
            self.amount_widget,
            self.term_widget,
            self.purpose_widget,
        )
        self._field(form, "Sample customer", self.customer_widget, 0)
        self._field(form, "Loan type", self.loan_type_widget, 1)
        self._field(form, "Loan amount (USD)", self.amount_widget, 2)
        self._field(form, "Repayment period (months)", self.term_widget, 3)
        self._field(form, "Purpose of the loan", self.purpose_widget, 4)
        ttk.Label(
            form,
            text="Use fictional sample data only. Amount must be over $0.",
            style="Hint.TLabel",
        ).grid(row=5, column=1, sticky="w", pady=(0, 5))

        review = ttk.LabelFrame(
            frame, text="Review", style="Section.TLabelframe", padding=(16, 12)
        )
        review.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        self.review_text = tk.StringVar(
            value="Your saved draft will appear here. It will not be submitted until you confirm."
        )
        ttk.Label(
            review,
            textvariable=self.review_text,
            style="Review.TLabel",
            wraplength=560,
            justify="left",
        ).pack(fill="x")

        actions = ttk.Frame(frame, style="Actions.TFrame")
        actions.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=0)
        self.create_button = ttk.Button(
            actions,
            text="Create draft",
            style="Pink.TButton",
            command=self.create_draft,
            state="disabled",
        )
        self.create_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.confirm_button = ttk.Button(
            actions,
            text="Confirm submission",
            style="Violet.TButton",
            command=self.confirm_submission,
            state="disabled",
        )
        self.confirm_button.grid(row=0, column=1, sticky="ew", padx=6)
        self.reset_button = ttk.Button(
            actions,
            text="Start over",
            style="Quiet.TButton",
            command=self.start_over,
            state="disabled",
        )
        self.reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))

        frame.columnconfigure(0, weight=1)
        self.load_customers()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["canvas"])
        style.configure("Actions.TFrame", background=COLORS["canvas"])
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
        style.configure("Subtitle.TLabel", foreground=COLORS["muted"])
        style.configure("Hint.TLabel", foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure(
            "Section.TLabelframe",
            background=COLORS["surface"],
            bordercolor=COLORS["border"],
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "Section.TLabelframe.Label",
            background=COLORS["canvas"],
            foreground=COLORS["violet"],
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "Status.TLabel",
            foreground=COLORS["muted"],
            background=COLORS["lavender"],
            padding=(10, 8),
        )
        style.configure(
            "Error.TLabel",
            foreground=COLORS["error"],
            background=COLORS["error_surface"],
            padding=(10, 8),
        )
        style.configure(
            "Review.TLabel",
            foreground=COLORS["ink"],
            background=COLORS["lavender"],
            padding=(12, 10),
            font=("Segoe UI", 10),
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

        style.configure(
            "Quiet.TButton",
            background=COLORS["surface"],
            foreground=COLORS["violet"],
            padding=(10, 9),
            bordercolor=COLORS["border"],
        )
        style.map(
            "Quiet.TButton",
            background=[("disabled", COLORS["canvas"]), ("active", COLORS["lavender"])],
            foreground=[("disabled", COLORS["muted"])],
        )

    @staticmethod
    def _field(frame: ttk.LabelFrame, label: str, widget: tk.Widget, row: int) -> None:
        ttk.Label(frame, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 14), pady=7
        )
        widget.grid(row=row, column=1, sticky="ew", pady=7)

    def _set_status(self, message: str, is_error: bool = False) -> None:
        self.status.set(message)
        self.status_label.configure(style="Error.TLabel" if is_error else "Status.TLabel")

    @staticmethod
    def _friendly_error(error: Exception) -> str:
        if isinstance(error, HTTPError):
            try:
                detail = json.loads(error.read().decode("utf-8")).get("detail")
            except (ValueError, AttributeError):
                detail = None
            return detail or f"The service returned an error ({error.code})."
        if isinstance(error, (URLError, TimeoutError)):
            return f"Could not reach the mock service at {API_URL}. Check the connection and retry."
        return str(error)

    def _set_form_enabled(self, enabled: bool) -> None:
        self.customer_widget.configure(state="readonly" if enabled else "disabled")
        self.loan_type_widget.configure(state="readonly" if enabled else "disabled")
        for widget in self.form_widgets[2:]:
            widget.configure(state="normal" if enabled else "disabled")
        self.create_button.configure(state="normal" if enabled else "disabled")

    def load_customers(self) -> None:
        self.retry_button.configure(state="disabled")
        self._set_status("Connecting to the mock service...")
        try:
            customers = api_request("/customers")
            self.customers = {f"{row['name']} (ID {row['id']})": row["id"] for row in customers}
            self.customer_widget.configure(values=list(self.customers))
            if self.customers:
                self.customer.set(next(iter(self.customers)))
                self._set_form_enabled(True)
                self._set_status(
                    "Connected. This demo uses fictional data and does not contact a bank."
                )
            else:
                self._set_status("No sample customers are available yet.", is_error=True)
        except (HTTPError, URLError, TimeoutError) as error:
            self._set_status(self._friendly_error(error), is_error=True)
            self.retry_button.configure(state="normal")

    def create_draft(self) -> None:
        amount_text = self.amount.get().strip().replace(",", "").replace("$", "")
        purpose = self.purpose.get().strip()
        try:
            amount = float(amount_text)
            term_months = int(self.term.get().strip())
        except ValueError:
            self._set_status(
                "Enter a valid loan amount and whole-number repayment period.", is_error=True
            )
            return
        if amount <= 0 or amount > 2_000_000:
            self._set_status(
                "Loan amount must be greater than $0 and no more than $2,000,000.",
                is_error=True,
            )
            return
        if term_months < 1 or term_months > 480:
            self._set_status(
                "Repayment period must be between 1 and 480 months.", is_error=True
            )
            return
        if len(purpose) < 5:
            self._set_status("Add a short purpose of at least 5 characters.", is_error=True)
            return

        try:
            payload = {
                "customer_id": self.customers[self.customer.get()],
                "loan_type": self.loan_type.get().lower(),
                "amount": amount,
                "term_months": term_months,
                "purpose": purpose,
            }
            application = api_request("/applications", "POST", payload)
            self.application_id = application["id"]
            self._set_form_enabled(False)
            self.create_button.configure(text="Draft created")
            self.confirm_button.configure(state="normal")
            self.reset_button.configure(state="normal")
            self.review_text.set(
                f"Draft #{self.application_id}  |  {application['customer_name']}\n"
                f"{self.loan_type.get()} loan  |  ${amount:,.2f}  |  {term_months} months\n"
                f"Purpose: {purpose}\n\nStatus: Draft only. Nothing has been submitted."
            )
            self._set_status("Review the details above. Confirm only if everything is correct.")
        except (KeyError, ValueError, HTTPError, URLError, TimeoutError) as error:
            self._set_status(
                f"Could not create the draft: {self._friendly_error(error)}", is_error=True
            )

    def start_over(self) -> None:
        if self.application_id is not None and not messagebox.askyesno(
            "Start a new application?",
            f"Draft #{self.application_id} will remain unsubmitted in the mock database. Start over?",
            parent=self.root,
        ):
            return
        self.application_id = None
        self.loan_type.set("Personal")
        self.amount.set("")
        self.term.set("36")
        self.purpose.set("")
        self.review_text.set(
            "Your saved draft will appear here. It will not be submitted until you confirm."
        )
        self.create_button.configure(text="Create draft")
        self.confirm_button.configure(state="disabled")
        self.reset_button.configure(state="disabled")
        self._set_form_enabled(bool(self.customers))
        self._set_status("Ready for a new mock application.")

    def confirm_submission(self) -> None:
        if self.application_id is None:
            return
        application = self.review_text.get()
        confirmed = messagebox.askyesno(
            "Review and confirm",
            f"Submit this mock application?\n\n{application}\n\n"
            "This only updates the local mock database. No real bank will be contacted.",
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
            self.review_text.set(
                self.review_text.get().replace(
                    "Status: Draft only. Nothing has been submitted.",
                    "Status: Submitted to the mock database.",
                )
            )
            self._set_status(f"Mock application #{application['id']} submitted successfully.")
        except (HTTPError, URLError, TimeoutError) as error:
            self._set_status(
                f"Could not submit the application: {self._friendly_error(error)}", is_error=True
            )


def main() -> None:
    root = tk.Tk()
    LoanApplicationWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
