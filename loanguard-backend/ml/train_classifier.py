"""
ml/train_classifier.py — Train and persist the LoanGuard AI multi-label risk classifier.

Run this script once to generate ml/model.pkl:
    python -m ml.train_classifier

Architecture:
  - TF-IDF Vectorizer (15,000 features, ngram_range=(1,3), sublinear_tf=True)
  - OneVsRestClassifier(LogisticRegression(C=1.5, class_weight='balanced'))
  - MultiLabelBinarizer for category labels
"""

from __future__ import annotations

import pickle
import random
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

CATEGORIES = [
    "hidden_fee_risk",
    "default_recovery_risk",
    "legal_clause_detection",
    "financial_entity_extraction",
    "power_imbalance_risk",
    "privacy_data_risk",
    "regulatory_compliance",
    "predatory_lending_signals",
]

# ---------------------------------------------------------------------------
# Synthetic training data templates per category
# ---------------------------------------------------------------------------
_TEMPLATES: dict[str, list[str]] = {
    "hidden_fee_risk": [
        "A processing fee of 3% will be deducted upfront from the loan amount.",
        "GST extra will be charged on all applicable fees and charges.",
        "Pre-closure fee of 4% will apply if loan is repaid before 12 months.",
        "Late payment charge of ₹500 per day will be levied on overdue amounts.",
        "Bounce charge of ₹1,000 will be applied for each dishonoured mandate.",
        "Penal interest of 3% per month will be charged on overdue EMIs.",
        "Documentation fee and stamp duty are payable by the borrower.",
        "Insurance premium mandatory and will be added to the loan amount.",
        "Annual maintenance charge of ₹500 applies on the loan account.",
        "Convenience fee of 2% is levied on each EMI payment.",
        "Cheque swap charge of ₹300 for any change in repayment instrument.",
        "Field visit charge of ₹500 for each recovery agent visit.",
        "Penal charges of 24% per annum on the outstanding overdue amount.",
        "Pre-closure charges shall be as applicable at the time of foreclosure.",
        "All fees and charges are subject to change at the lender's discretion.",
    ],
    "default_recovery_risk": [
        "In case of default, the lender may accelerate the entire outstanding loan.",
        "The lender reserves the right to seize and sell the pledged asset without notice.",
        "Upon default, the account will be classified as NPA under RBI guidelines.",
        "Recovery agent will be appointed to collect overdue amounts from the borrower.",
        "The lender may initiate SARFAESI proceedings to recover the outstanding dues.",
        "Cross default applies: default in any loan triggers default in all loans.",
        "The lender may refer the matter to DRT or Lok Adalat for recovery.",
        "Repossession of the vehicle will occur if 3 consecutive EMIs are missed.",
        "Full repayment immediately becomes due upon occurrence of any event of default.",
        "Legal action including criminal proceedings may be initiated upon default.",
        "The borrower shall be liable for all recovery costs including legal fees.",
        "Asset seizure will be carried out without prior notice to the borrower.",
        "Material adverse change in borrower's financial condition triggers acceleration.",
        "Credit deterioration shall be deemed an event of default under this agreement.",
        "Attachment of property will be pursued through appropriate legal channels.",
    ],
    "legal_clause_detection": [
        "Force majeure events shall excuse performance of obligations under this agreement.",
        "The borrower shall indemnify the lender against all losses and damages.",
        "Any dispute shall be subject to mandatory arbitration under Indian Arbitration Act.",
        "This agreement shall be governed by the laws of Maharashtra, India.",
        "The borrower irrevocably waives the right to challenge lender's calculations.",
        "This constitutes the entire agreement superseding all prior communications.",
        "Severability clause: if any provision is invalid, remaining provisions stand.",
        "The lender may modify terms with 30 days notice to the borrower.",
        "Limitation of liability: lender shall not be liable for indirect damages.",
        "Jurisdiction clause: courts of Mumbai shall have exclusive jurisdiction.",
        "The arbitration clause requires disputes to be resolved in New Delhi.",
        "Hold harmless provision protects lender from third-party claims.",
        "Amendment clause allows lender to change terms at any time.",
        "The prepayment clause restricts early repayment for first 12 months.",
        "Force majeure includes natural disasters, pandemics, and regulatory changes.",
    ],
    "financial_entity_extraction": [
        "The EMI of ₹4,707 is due on the 5th of every month.",
        "Loan amount sanctioned is ₹50,000 at an interest rate of 24% per annum.",
        "CIBIL score below 650 may result in rejection of the loan application.",
        "The NACH mandate authorizes monthly debit of EMI from the bank account.",
        "MCLR rate is 8.5% and the spread is 3.5% making the effective rate 12%.",
        "LTV ratio shall not exceed 80% of the market value of the property.",
        "SOFR plus a spread of 250 basis points determines the floating interest rate.",
        "Moratorium period of 3 months applies before EMI payments commence.",
        "The repayment schedule attached as Annexure A shows amortisation details.",
        "Balloon payment of ₹20,000 is due at the end of the loan tenure.",
        "ECS mandate is registered for automatic EMI deduction every month.",
        "The loan disbursement will be made directly to the supplier's account.",
        "Bullet repayment of principal is due at maturity of the instrument.",
        "Drawdown of ₹1,00,000 will be made in tranches as per the schedule.",
        "The tenor of the loan is 24 months from the date of disbursement.",
    ],
    "power_imbalance_risk": [
        "The lender, at its sole discretion, may modify any terms of this agreement.",
        "The borrower irrevocably authorises the lender to debit any account.",
        "The lender may, at any time and without notice, demand full repayment.",
        "The lender has the unilateral right to change the interest rate.",
        "The lender may revoke any facility at its absolute discretion.",
        "Without prior notice, the lender may cancel the approved credit limit.",
        "The lender may, without reason, refuse to disburse the approved amount.",
        "As deemed fit by the lender, additional security may be demanded.",
        "The borrower irrevocably appoints the lender as attorney to execute documents.",
        "The lender's determination shall be final and binding on the borrower.",
        "Unilaterally, the lender may alter the repayment schedule.",
        "The lender may, as determined by the lender, change collection methods.",
        "Right to modify all fees and charges rests exclusively with the lender.",
        "The lender may, without cause, report the borrower to credit bureaus.",
        "Irrevocable consent to data sharing with third parties is hereby granted.",
    ],
    "privacy_data_risk": [
        "The app requires access to SMS to verify loan repayments and track usage.",
        "Contact access is required to enable communication with the borrower.",
        "Location access must be granted for verification and risk assessment purposes.",
        "Gallery access enables document verification and identity confirmation.",
        "Device data including call logs may be accessed for credit assessment.",
        "Behavior monitoring of app usage patterns is used for credit scoring.",
        "Under DPDP Act, personal data will be processed with your consent.",
        "Browsing data may be shared with third-party credit assessment agencies.",
        "Microphone access is required for voice-based KYC verification.",
        "Camera access enables selfie-based identity verification.",
        "Phone data including IMEI number will be collected for fraud prevention.",
        "Data sharing with our partner NBFCs and banks is part of credit assessment.",
        "Credit information will be shared with all credit bureaus as required.",
        "Usage monitoring helps us provide personalized loan offers.",
        "Third-party sharing of behavioral data may occur for marketing purposes.",
    ],
    "regulatory_compliance": [
        "This NBFC is registered with RBI under the Non-Banking Financial Companies Act.",
        "As per RBI guidelines on digital lending, all disbursements are direct.",
        "The DLA (digital lending app) complies with RBI master directions.",
        "LSP (lending service provider) is responsible for customer interface.",
        "Key Fact Statement (KFS) is provided to the borrower before signing.",
        "Direct disbursement to borrower's bank account as per RBI circular.",
        "Grievance redressal officer contact details are provided in this agreement.",
        "The cooling-off period of 3 days allows borrower to cancel without penalty.",
        "Annual Percentage Rate (APR) including all charges is disclosed herein.",
        "Total cost of credit is disclosed upfront as required by RBI regulations.",
        "Nodal officer for grievance redressal is available at the registered address.",
        "Direct repayment to the regulated entity and not through the LSP.",
        "RBI circular on outsourcing of financial services is complied with.",
        "NBFC regulations prohibit collection of any upfront fees before disbursement.",
        "Lending service provider agreement is registered with the parent NBFC.",
    ],
    "predatory_lending_signals": [
        "Processing fee of 25% will be deducted upfront before loan disbursement.",
        "Hidden charges may apply as determined by the lender from time to time.",
        "Insurance bundled with the loan is mandatory and non-refundable.",
        "Upfront deduction of ₹2,700 from the sanctioned amount of ₹10,000.",
        "Forced insurance coverage adds ₹1,500 to the total loan cost.",
        "Penalty on penalty is applied when two consecutive EMIs are missed.",
        "Undisclosed charges will be debited without prior notification.",
        "Third-party collection agency fee is borne by the borrower.",
        "Excessive penalty of 5% per week on overdue amounts is applicable.",
        "Insurance premium is mandatory and bundled with the loan disbursement.",
        "Hidden deduction reduces the net disbursement significantly.",
        "Coercive recovery practices including contact with family members are used.",
        "Upfront fee deduction of 30% leaves borrower with only 70% of approved amount.",
        "Unauthorised recovery through third parties occurs without court order.",
        "Compound penalty structure results in rapidly escalating dues.",
    ],
}


def generate_dataset() -> tuple[list[str], list[list[str]]]:
    """Generate synthetic training data."""
    texts: list[str] = []
    labels: list[list[str]] = []

    # Single-category samples (120 per category)
    for cat, templates in _TEMPLATES.items():
        for _ in range(120):
            tmpl = random.choice(templates)
            # Add slight variation
            variation = tmpl + " " + random.choice([
                "This clause is binding.",
                "The borrower acknowledges and agrees.",
                "Terms and conditions apply.",
                "Subject to applicable laws.",
                "",
            ])
            texts.append(variation.strip())
            labels.append([cat])

    # Multi-label samples (120 combos)
    cat_list = list(_TEMPLATES.keys())
    for _ in range(120):
        n_cats = random.randint(2, 3)
        selected_cats = random.sample(cat_list, n_cats)
        combined = " ".join(
            random.choice(_TEMPLATES[cat]) for cat in selected_cats
        )
        texts.append(combined)
        labels.append(selected_cats)

    # Negative samples (35 — neutral loan docs)
    neutral_samples = [
        "The borrower agrees to repay the loan in equal monthly instalments.",
        "This agreement is entered into on the date mentioned above.",
        "The lender shall disburse the loan amount within 24 hours of approval.",
        "Both parties agree to the terms and conditions set forth herein.",
        "The loan amount, interest rate, and tenure are as specified in the schedule.",
        "Repayment shall be made via NACH debit from the borrower's savings account.",
        "The borrower shall maintain a valid bank account throughout the loan tenure.",
        "The lender shall provide a statement of account on request.",
        "This agreement is subject to the laws of India.",
        "The borrower's signature below acknowledges reading and understanding the terms.",
        "EMI payments are due on the 5th of each month.",
        "The loan application has been reviewed and approved as per policy.",
        "Customer support is available Monday to Saturday 9 AM to 6 PM.",
        "The interest rate is fixed for the entire duration of the loan.",
        "Prepayment is allowed without any additional charges.",
    ]
    for _ in range(35):
        texts.append(random.choice(neutral_samples))
        labels.append([])  # No risk category

    return texts, labels


def train_and_save(output_path: str | Path = "ml/model.pkl") -> None:
    """Train the classifier and persist to pickle file."""
    print("Generating synthetic training data...")
    texts, labels = generate_dataset()
    print(f"Dataset size: {len(texts)} samples")

    # Binarize labels
    mlb = MultiLabelBinarizer(classes=CATEGORIES)
    Y = mlb.fit_transform(labels)

    # Build pipeline
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=15_000,
            ngram_range=(1, 3),
            sublinear_tf=True,
            min_df=1,
            strip_accents="unicode",
            analyzer="word",
        )),
        ("clf", OneVsRestClassifier(
            LogisticRegression(
                C=1.5,
                class_weight="balanced",
                max_iter=1000,
                solver="lbfgs",
                random_state=42,
            )
        )),
    ])

    # Train/test split
    X_train, X_test, Y_train, Y_test = train_test_split(
        texts, Y, test_size=0.15, random_state=42
    )

    print("Training classifier...")
    pipeline.fit(X_train, Y_train)

    # Evaluate
    Y_pred = pipeline.predict(X_test)
    print("\nClassification Report:")
    print(
        classification_report(
            Y_test,
            Y_pred,
            target_names=CATEGORIES,
            zero_division=0,
        )
    )

    # Persist
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump({"pipeline": pipeline, "mlb": mlb}, f)
    print(f"\nModel saved to {output_path}")


if __name__ == "__main__":
    train_and_save()
