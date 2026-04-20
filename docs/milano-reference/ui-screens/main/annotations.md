# Milano Reference — Main Module

Screenshots from the Milano Salon software main entry point, captured from the Salon Lyol installation on 2026-04-19.

---

## Login Screen

![Login](./Screenshot%202026-04-19%20at%204.34.25%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.34.25 PM.png`

The Milano splash/login screen. Staff authenticate with a **Staff Code** and **Password**. The top bar shows the software version and current date/time. The Salon Lyol ("LYOU") logo appears bottom-right.

**Domain notes:**
- Each staff member has their own login — the `Staff` entity needs credentials (staff_code, password_hash).
- Version string in the top bar suggests Milano tracks software version per installation — relevant context for migration planning.

---

## Main Menu

![Main Menu](./Screenshot%202026-04-19%20at%204.35.58%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.35.58 PM.png`

Post-login main menu. Left sidebar navigation:

| Menu Item | Notes |
|-----------|-------|
| **Appointment Book** | Central feature — opens the provider/day grid |
| **CRM** | Customer Relation Management — client records, history |
| **Reports** | Reporting module |
| **Data Control** | Administrative / configuration |
| **Licence Management** | Software licensing |
| **QuickSale** | POS / point-of-sale shortcut |
| **Links** | External links |

**Domain notes:**
- The top-level module split maps closely to the phased roadmap: Appointment Book (Phase 1), CRM email/chat (Phase 2), Reporting (Phase 2), QuickSale/POS (Phase 2).
- `Data Control` is the closest analogue to our admin/tenant configuration area.
