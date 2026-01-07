# Multi-Step Flows

This document defines the three multi-step flows the pharmacy agent executes. Each flow represents a complete customer journey from initial request to resolution.

---

## Flow A: Medication Info (Customer Service)

**User Goal:** Get factual information about a medication (ingredients, dosage, warnings, prescription requirement).

### Sequence Diagram

```
User                    Agent                      Tools
 │                        │                          │
 ├─ "Tell me about X" ───►│                          │
 │                        ├─ get_medication_by_name ─►│
 │                        │◄─ medication details ────┤
 │◄─ factual info ───────┤                          │
 │                        │                          │
 │  (optional follow-up)  │                          │
 ├─ "Should I take it?" ─►│                          │
 │◄─ REFUSAL + redirect ─┤ (no tool call)           │
```

### Steps

1. **User asks about medication** - e.g., "What is Ibuprofen?", "Tell me about צטיריזין"
2. **Agent calls `get_medication_by_name(name)`** - Resolves medication by EN/HE name
3. **Agent returns factual info** - Active ingredients, dosage, warnings, Rx requirement
4. **If user requests medical advice** - Agent refuses and redirects to healthcare professional

### Tool Calls

| Step | Tool | Input | Output |
|------|------|-------|--------|
| 2 | `get_medication_by_name` | `{"name": "Ibuprofen"}` | Medication details (dosage, warnings, rx_required) |

### Example Conversation

```
User: "What is Ibuprofen used for?"

Agent: [calls get_medication_by_name("Ibuprofen")]

Agent: "Ibuprofen contains the active ingredient Ibuprofen.

Dosage: Take 200-400mg every 4-6 hours as needed. Maximum 1200mg/day.

Warnings: Do not use if allergic to NSAIDs. Avoid with stomach ulcers.

This medication does not require a prescription (OTC)."

---

User: "Should I take it for my headache?"

Agent: "I cannot provide medical advice or recommendations for your specific
condition. Please consult with a healthcare professional or pharmacist who
can evaluate your situation and provide appropriate guidance."
```

### Edge Cases

- **NOT_FOUND**: Medication name not in database → "I couldn't find a medication named 'X'. Please check the spelling or try another name."
- **AMBIGUOUS**: Multiple matches → "I found multiple medications. Did you mean X or Y?"

---

## Flow B: Inventory Check (Inventory Control)

**User Goal:** Check if a specific medication is in stock.

### Sequence Diagram

```
User                    Agent                      Tools
 │                        │                          │
 ├─ "Do you have X?" ────►│                          │
 │                        ├─ get_medication_by_name ─►│
 │                        │◄─ medication details ────┤
 │                        ├─ check_inventory ────────►│
 │                        │◄─ stock info ────────────┤
 │◄─ availability ───────┤                          │
```

### Steps

1. **User asks about stock** - e.g., "Is Amoxicillin in stock?", "יש לכם איבופרופן?"
2. **Agent calls `get_medication_by_name(name)`** - Resolves medication to get med_id
3. **Agent calls `check_inventory(med_id)`** - Checks stock at default store
4. **Agent returns availability** - In stock (qty) or out of stock (with restock ETA if available)

### Tool Calls

| Step | Tool | Input | Output |
|------|------|-------|--------|
| 2 | `get_medication_by_name` | `{"name": "Amoxicillin"}` | `{med_id: 2, ...}` |
| 3 | `check_inventory` | `{"med_id": 2}` | `{in_stock: false, qty: 0, restock_eta: "2025-01-15"}` |

### Example Conversation

```
User: "Do you have Amoxicillin in stock?"

Agent: [calls get_medication_by_name("Amoxicillin")]
       [calls check_inventory(med_id=2)]

Agent: "Amoxicillin is currently out of stock. Expected restock date: January 15, 2025.

Note: Amoxicillin requires a prescription."

---

User: "What about Cetirizine?"

Agent: [calls get_medication_by_name("Cetirizine")]
       [calls check_inventory(med_id=5)]

Agent: "Cetirizine is in stock (200 units available).

This medication is available over-the-counter (no prescription needed)."
```

### Edge Cases

- **NOT_FOUND (medication)**: → "I couldn't find a medication named 'X'."
- **NOT_FOUND (inventory)**: → "I don't have inventory information for this medication."
- **Low stock**: qty <= 10 → "Cetirizine is in stock but limited quantity available (5 units)."

---

## Flow C: Prescription Status/Refill (Prescription Management)

**User Goal:** View prescription history or check refill eligibility.

### Sequence Diagram

```
User                    Agent                      Tools
 │                        │                          │
 ├─ "My prescriptions?" ─►│                          │
 │◄─ "What's your email?" │ (needs identifier)       │
 │                        │                          │
 ├─ "david@example.com" ─►│                          │
 │                        ├─ prescription_management ►│
 │                        │  (action=LIST)           │
 │                        │◄─ prescription list ─────┤
 │◄─ "You have 2 Rx..." ─┤                          │
 │                        │                          │
 ├─ "Can I refill #1?" ──►│                          │
 │                        ├─ prescription_management ►│
 │                        │  (action=REFILL_STATUS)  │
 │                        │◄─ refill info ───────────┤
 │◄─ "Yes, 2 refills..." ┤                          │
```

### Steps

1. **User asks about prescriptions** - e.g., "What prescriptions do I have?"
2. **Agent asks for identifier** (if not provided) - "Please provide your email or phone number"
3. **User provides identifier** - e.g., "david.cohen@example.com"
4. **Agent calls `prescription_management(action=LIST, email=...)`** - Retrieves prescriptions
5. **Agent shows prescription list** - Medication names, refills remaining, status
6. **User asks about specific prescription** (optional) - "Can I refill the Amoxicillin?"
7. **Agent calls `prescription_management(action=REFILL_STATUS, presc_id=...)`** - Checks refill status
8. **Agent returns refill info** - Eligibility, refills remaining, constraints

### Tool Calls

| Step | Tool | Input | Output |
|------|------|-------|--------|
| 4 | `prescription_management` | `{"action": "LIST", "email": "david.cohen@example.com"}` | List of prescriptions |
| 7 | `prescription_management` | `{"action": "REFILL_STATUS", "user_email": "...", "presc_id": 1}` | Refill eligibility |

### Example Conversation

```
User: "What prescriptions do I have?"

Agent: "I'll need your email or phone number to look up your prescriptions."

---

User: "david.cohen@example.com"

Agent: [calls prescription_management(action=LIST, email="david.cohen@example.com")]

Agent: "I found 2 active prescriptions for David Cohen:

1. Amoxicillin - 2 refills remaining (active)
2. Metformin - 5 refills remaining (active)

Would you like to check the refill status for any of these?"

---

User: "Can I refill the Amoxicillin?"

Agent: [calls prescription_management(action=REFILL_STATUS, user_email="david.cohen@example.com", presc_id=1)]

Agent: "Yes, your Amoxicillin prescription is eligible for refill.
You have 2 refills remaining.

Note: Amoxicillin requires a valid prescription. Please ensure your
prescription is current before requesting a refill."
```

### Edge Cases

- **UNAUTHORIZED**: User not found → "I couldn't find an account with that email/phone. Please verify your information."
- **No prescriptions**: User exists but no prescriptions → "You don't have any prescriptions on file."
- **Completed**: No refills left → "This prescription has been completed (0 refills remaining)."
- **Expired**: Prescription expired → "This prescription has expired. Please consult your doctor for a new prescription."

---

## Policy Enforcement

All flows enforce the following policies:

1. **No Medical Advice**: Agent refuses to recommend treatments or diagnose conditions
2. **No Purchase Encouragement**: Agent provides factual info without pushing sales
3. **Facts Only**: All responses come from database, no speculation
4. **Bilingual**: Agent responds in the same language as the user's query

### Refusal Examples

```
User: "What should I take for my cold?"
Agent: "I cannot recommend specific medications for your condition. Please
consult a healthcare professional who can evaluate your symptoms and
provide appropriate treatment options."

User: "Is Ibuprofen better than Tylenol?"
Agent: "I cannot provide comparative medical advice. Both medications have
different active ingredients and uses. Please consult a pharmacist or
healthcare professional for guidance on which is appropriate for your needs."
```
