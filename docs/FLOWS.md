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

| Step | Tool                     | Input                              | Output                                                                                                                                     |
| ---- | ------------------------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 2    | `get_medication_by_name` | `{"medication_name": "Ibuprofen"}` | `{success: true, medication: {med_id, name_en, name_he, active_ingredients, dosage_en, dosage_he, rx_required, warnings_en, warnings_he}}` |

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

| Step | Tool                     | Input                                | Output                                                                                                                                          |
| ---- | ------------------------ | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 2    | `get_medication_by_name` | `{"medication_name": "Amoxicillin"}` | `{success: true, medication: {med_id: 2, name_en, name_he, ...}}`                                                                               |
| 3    | `check_inventory`        | `{"medication_id": 2}`               | `{success: true, inventory: {med_id, store_id, medication_name_en, medication_name_he, in_stock: false, qty: null, restock_eta: "2026-01-15"}}` |

**Note:** When out of stock, `qty` is `null` (not `0`) and `restock_eta` is provided. When in stock, `qty` has the count and `restock_eta` is `null`.

### Example Conversation

```
User: "Do you have Amoxicillin in stock?"

Agent: [calls get_medication_by_name("Amoxicillin")]
       [calls check_inventory(med_id=2)]

Agent: "Amoxicillin is currently out of stock. Expected restock date: January 15, 2026.

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
4. **Agent calls `prescription_management(action=LIST, user_identifier=...)`** - Retrieves prescriptions
5. **Agent shows prescription list** - Medication names, refills remaining, status
6. **User asks about specific prescription** (optional) - "Can I refill the Amoxicillin?"
7. **Agent calls `prescription_management(action=REFILL_STATUS, prescription_id=...)`** - Checks refill status
8. **Agent returns refill info** - Eligibility, refills remaining, constraints

### Tool Calls

| Step | Tool                      | Input                                                                         | Output                                                                                                                                                          |
| ---- | ------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 4    | `prescription_management` | `{"action": "LIST", "user_identifier": "david.cohen@example.com"}`            | `{success: true, user_name: "David Cohen", prescriptions: [{presc_id, med_id, medication_name_en, medication_name_he, refills_left, status, can_refill}, ...]}` |
| 7    | `prescription_management` | `{"action": "REFILL_STATUS", "user_identifier": "...", "prescription_id": 1}` | `{success: true, prescription: {...}, refill_eligible: true, reason: "2 refill(s) available"}`                                                                  |

### Example Conversation

```
User: "What prescriptions do I have?"

Agent: "I'll need your email or phone number to look up your prescriptions."

---

User: "david.cohen@example.com"

Agent: [calls prescription_management(action=LIST, user_identifier="david.cohen@example.com")]

Agent: "I found 2 active prescriptions for David Cohen:

1. Amoxicillin - 2 refills remaining (active)
2. Metformin - 5 refills remaining (active)

Would you like to check the refill status for any of these?"

---

User: "Can I refill the Amoxicillin?"

Agent: [calls prescription_management(action=REFILL_STATUS, user_identifier="david.cohen@example.com", prescription_id=1)]

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

---

# Tool Specifications (Required Documentation)

This section documents each tool used by the agent, including purpose, inputs, output schemas, error handling, and fallback behavior.

---

## Tool: `get_medication_by_name`

### 1) Purpose

Look up factual medication information by English or Hebrew name. Used when users ask about a medication's ingredients, dosage instructions, warnings, or prescription requirements.

### 2) Inputs

| Parameter         | Type  | Required | Description                                                              |
| ----------------- | ----- | -------: | ------------------------------------------------------------------------ |
| `medication_name` | `str` |      Yes | The name of the medication to search for (English or Hebrew, partial OK) |

### 3) Output Schema (Success)

**Shape:**

```json
{
  "success": true,
  "medication": {
    "med_id": 1,
    "name_en": "Ibuprofen",
    "name_he": "איבופרופן",
    "active_ingredients": "Ibuprofen 200mg",
    "dosage_en": "Take 200-400mg every 4-6 hours...",
    "dosage_he": "קח 200-400 מ\"ג כל 4-6 שעות...",
    "rx_required": false,
    "warnings_en": "Do not use if allergic to NSAIDs...",
    "warnings_he": "אין להשתמש אם יש רגישות ל-NSAIDs..."
  }
}
```

**Fields:**

| Field                           | Type   | Nullable | Description                      |
| ------------------------------- | ------ | -------: | -------------------------------- |
| `success`                       | `bool` |       No | Always `true` for success        |
| `medication`                    | object |       No | Medication details object        |
| `medication.med_id`             | `int`  |       No | Unique medication identifier     |
| `medication.name_en`            | `str`  |       No | Medication name in English       |
| `medication.name_he`            | `str`  |       No | Medication name in Hebrew        |
| `medication.active_ingredients` | `str`  |       No | Active ingredients list          |
| `medication.dosage_en`          | `str`  |       No | Dosage instructions in English   |
| `medication.dosage_he`          | `str`  |       No | Dosage instructions in Hebrew    |
| `medication.rx_required`        | `bool` |       No | Whether prescription is required |
| `medication.warnings_en`        | `str`  |       No | Warning text in English          |
| `medication.warnings_he`        | `str`  |       No | Warning text in Hebrew           |

### 4) Error Handling

**Shape (errors):**

```json
{
  "success": false,
  "error_code": "NOT_FOUND",
  "error_message": "No medication found matching 'xyz'",
  "query": "xyz"
}
```

**Error codes:**

| Code        | When                             | Additional Fields                                   |
| ----------- | -------------------------------- | --------------------------------------------------- |
| `NOT_FOUND` | Empty query or no matches found  | `query` (when non-empty search term was used)       |
| `AMBIGUOUS` | Multiple medications match       | `query`, `suggestions`: list of matching medication names |
| `INTERNAL`  | Unexpected database/system error | —                                                   |

### 5) Fallback Behavior

- **Exact match first**: Searches `LOWER(name_en) = LOWER(?)` OR `name_he = ?` (Hebrew is case-sensitive)
- **Partial match fallback**: If no exact match, uses `LIKE %query%` pattern
- **Ambiguity handling**: If multiple matches found, returns `AMBIGUOUS` error with `suggestions` array containing all matches formatted as "name_en (name_he)"
- **Empty input**: Returns `NOT_FOUND` with message "Medication name cannot be empty" (no `query` field included)

---

## Tool: `check_inventory`

### 1) Purpose

Check if a medication is in stock at the pharmacy. Used when users ask about medication availability. Accepts either a medication ID (from a previous `get_medication_by_name` call) or a medication name for convenience.

### 2) Inputs

| Parameter         | Type        | Required | Description                                           |
| ----------------- | ----------- | -------: | ----------------------------------------------------- |
| `medication_id`   | `int\|null` |       No | Medication ID from `get_medication_by_name` result    |
| `medication_name` | `str\|null` |       No | Medication name (alternative to ID, will be resolved) |
| `store_id`        | `int`       |       No | Store ID to check (default: `1`)                      |

**Note:** At least one of `medication_id` or `medication_name` must be provided. If both given, `medication_id` takes precedence.

### 3) Output Schema (Success)

**Shape:**

```json
{
  "success": true,
  "inventory": {
    "med_id": 2,
    "store_id": 1,
    "medication_name_en": "Amoxicillin",
    "medication_name_he": "אמוקסיצילין",
    "in_stock": false,
    "qty": null,
    "restock_eta": "2026-01-15"
  }
}
```

**Fields:**

| Field                          | Type        | Nullable | Description                                 |
| ------------------------------ | ----------- | -------: | ------------------------------------------- |
| `success`                      | `bool`      |       No | Always `true` for success                   |
| `inventory`                    | object      |       No | Inventory details object                    |
| `inventory.med_id`             | `int`       |       No | Medication identifier                       |
| `inventory.store_id`           | `int`       |       No | Store identifier                            |
| `inventory.medication_name_en` | `str`       |       No | Medication name in English                  |
| `inventory.medication_name_he` | `str`       |       No | Medication name in Hebrew                   |
| `inventory.in_stock`           | `bool`      |       No | Whether medication is currently in stock    |
| `inventory.qty`                | `int\|null` |      Yes | Quantity available (null when out of stock) |
| `inventory.restock_eta`        | `str\|null` |      Yes | Expected restock date (null when in stock)  |

**Important:** When `in_stock=false`, `qty` is `null` (not `0`) and `restock_eta` may be provided. When `in_stock=true`, `qty` contains the count and `restock_eta` is `null`.

### 4) Error Handling

**Shape (errors):**

```json
{
  "success": false,
  "error_code": "NOT_FOUND",
  "error_message": "Medication 'xyz' not found"
}
```

**Error codes:**

| Code            | When                                                   |
| --------------- | ------------------------------------------------------ |
| `INVALID_STATE` | Neither `medication_id` nor `medication_name` provided |
| `NOT_FOUND`     | Medication name resolution failed (no match)           |
| `NOT_FOUND`     | No inventory record exists for the medication at store |
| `INTERNAL`      | Unexpected database/system error                       |

### 5) Fallback Behavior

- **Name resolution**: If `medication_id` is absent and `medication_name` is provided:
  - Exact match first (`LOWER(name_en) = LOWER(?)` OR `name_he = ?`)
  - Else partial match using `LIKE %query%` and returns **first match only**
- **Recommendation**: Prefer calling with `medication_id` from a prior `get_medication_by_name` call to avoid ambiguous matches
- **Default store**: If `store_id` not specified, defaults to store `1`

---

## Tool: `prescription_management`

### 1) Purpose

Manage user prescriptions: list all prescriptions for an identified user, or check refill eligibility for a specific prescription. Requires user identification via email or phone number.

### 2) Inputs

| Parameter         | Type        |                  Required | Description                                |
| ----------------- | ----------- | ------------------------: | ------------------------------------------ |
| `user_identifier` | `str`       |                       Yes | User's email address or phone number       |
| `action`          | `str`       |                       Yes | `"LIST"` or `"REFILL_STATUS"`              |
| `prescription_id` | `int\|null` | Yes (for `REFILL_STATUS`) | Prescription ID to check refill status for |

### 3) Output Schema (Success)

#### For `action="LIST"`:

**Shape:**

```json
{
  "success": true,
  "user_name": "David Cohen",
  "prescriptions": [
    {
      "presc_id": 1,
      "med_id": 2,
      "medication_name_en": "Amoxicillin",
      "medication_name_he": "אמוקסיצילין",
      "refills_left": 2,
      "status": "active",
      "can_refill": true
    }
  ]
}
```

**Fields:**

| Field                                | Type    | Nullable | Description                                       |
| ------------------------------------ | ------- | -------: | ------------------------------------------------- |
| `success`                            | `bool`  |       No | Always `true` for success                         |
| `user_name`                          | `str`   |       No | User's name from database                         |
| `prescriptions`                      | `array` |       No | List of prescription objects (may be empty)       |
| `prescriptions[].presc_id`           | `int`   |       No | Unique prescription identifier                    |
| `prescriptions[].med_id`             | `int`   |       No | Medication identifier                             |
| `prescriptions[].medication_name_en` | `str`   |       No | Medication name in English                        |
| `prescriptions[].medication_name_he` | `str`   |       No | Medication name in Hebrew                         |
| `prescriptions[].refills_left`       | `int`   |       No | Number of refills remaining                       |
| `prescriptions[].status`             | `str`   |       No | Status: `"active"`, `"completed"`, or `"expired"` |
| `prescriptions[].can_refill`         | `bool`  |       No | Whether this prescription can be refilled now     |

#### For `action="REFILL_STATUS"`:

**Shape:**

```json
{
  "success": true,
  "prescription": {
    "presc_id": 1,
    "med_id": 2,
    "medication_name_en": "Amoxicillin",
    "medication_name_he": "אמוקסיצילין",
    "refills_left": 2,
    "status": "active",
    "can_refill": true
  },
  "refill_eligible": true,
  "reason": "2 refill(s) available"
}
```

**Fields:**

| Field             | Type   | Nullable | Description                                      |
| ----------------- | ------ | -------: | ------------------------------------------------ |
| `success`         | `bool` |       No | Always `true` for success                        |
| `prescription`    | object |       No | Prescription details (same schema as LIST items) |
| `refill_eligible` | `bool` |       No | Whether refill is currently allowed              |
| `reason`          | `str`  |       No | Human-readable explanation of eligibility        |

**Reason values:**

- `"X refill(s) available"` — eligible, X refills remaining
- `"Prescription is completed"` — not eligible, status is completed
- `"Prescription is expired"` — not eligible, status is expired
- `"No refills remaining"` — not eligible, refills_left is 0

### 4) Error Handling

**Shape (errors):**

```json
{
  "success": false,
  "error_code": "UNAUTHORIZED",
  "error_message": "User not found with identifier: xyz@example.com"
}
```

**Error codes:**

| Code            | When                                                      |
| --------------- | --------------------------------------------------------- |
| `INVALID_STATE` | Invalid action (not `LIST` or `REFILL_STATUS`)            |
| `UNAUTHORIZED`  | User not found with given email/phone                     |
| `NOT_FOUND`     | `prescription_id` not provided for `REFILL_STATUS` action |
| `NOT_FOUND`     | Prescription not found or doesn't belong to user          |
| `INTERNAL`      | Unexpected database/system error                          |

### 5) Fallback Behavior

- **User lookup**:
  - Email: case-insensitive (`LOWER(email) = LOWER(?)`)
  - Phone: exact match (`phone = ?`)
- **Unknown status handling**: If database contains unexpected status value, defaults to `"expired"` and logs a warning
- **Can refill calculation**: `can_refill = (status == "active") AND (refills_left > 0)`
- **Empty prescriptions**: If user exists but has no prescriptions, returns empty `prescriptions` array (not an error)
