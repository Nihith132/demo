"""
Script to ingest ESI protocols into vector store.
Run: python utils/ingest_esi.py
"""

from __future__ import annotations

from database import SessionLocal

# ESI protocol text (from the user's input)
ESI_PROTOCOL_TEXT = """
Overview of the Emergency Severity Index (ESI)
The ESI is a 5-level emergency department triage algorithm that provides clinically relevant stratification of patients into five groups from 1 (most urgent) to 5 (least urgent) based on acuity and resource needs.

Decision Point A: ESI Level 1 (Resuscitation)

Definition: The patient requires immediate life-saving intervention.

Clinical Criteria: The patient is pulseless, apneic, has severe respiratory distress, SPO2 < 90%, is unresponsive, or requires immediate intubation or hemodynamic interventions (e.g., fluid resuscitation for shock).

Action: Immediate bedside evaluation by a physician.

Keywords for AI: Cardiac arrest, respiratory arrest, severe trauma, unresponsive, stroke with airway compromise, active massive bleeding, overdose with hypoventilation.

Decision Point B: ESI Level 2 (Emergent)

Definition: The patient is in a high-risk situation, is confused/lethargic/disoriented, or is in severe pain or distress. They should not wait to be seen.

Clinical Criteria: High-risk conditions that could easily deteriorate. Severe pain is defined as self-reported 7/10 or higher.

Action: Placement in a treatment area rapidly; physician evaluation within 10-15 minutes.

Keywords for AI: Chest pain (suspected cardiac), signs of stroke (but airway intact), severe abdominal pain, suicidal ideation, ectopic pregnancy, newborn with fever, sudden severe headache, major fractures.

Decision Point C: The Resource Assessment (For Levels 3, 4, and 5)
If the patient does not meet ESI 1 or 2 criteria, the triage decision is based on the number of projected "resources" required to reach a disposition (discharge or admit).

What counts as ONE resource:

Labs (blood or urine) - Note: A complete blood count and a metabolic panel together count as only ONE resource (Labs).

ECG / X-rays

CT / MRI / Ultrasound

IV Fluids (hydration)

IV, IM, or Nebulized medications

Specialty consultation

Simple procedure (e.g., 1 laceration repair) or Complex procedure (e.g., conscious sedation).

What DOES NOT count as a resource:

History and physical exam (including pelvic)

Point-of-care testing (blood glucose, quick strep)

Saline lock (IV access without fluids)

PO (oral) medications, tetanus immunization, prescription refills

Phone call to PCP

Simple wound care (crutches, splints, slings)

Decision Point D: ESI Level 3 (Urgent)

Definition: The patient requires two or more distinct resources (as defined above).

Clinical Criteria: Stable vital signs, but requires multiple diagnostic tests or interventions to determine the problem.

Action: Can wait a short time for a bed, but needs a thorough workup.

Keywords for AI: Undifferentiated abdominal pain (needs labs and CT), minor trauma (needs x-ray and laceration repair), pneumonia symptoms (needs x-ray, labs, IV antibiotics).

Vital Sign Exception: If a patient requires 2+ resources but has vital signs in the danger zone (e.g., heart rate > 100, respiratory rate > 20), the AI should consider up-triage to ESI 2.

Decision Point E: ESI Level 4 (Less Urgent)

Definition: The patient requires exactly one resource (as defined above).

Clinical Criteria: Stable, minor conditions requiring limited investigation.

Action: Can safely wait.

Keywords for AI: Simple minor trauma (needs 1 x-ray), urinary tract infection symptoms (needs 1 urinalysis), minor throat pain (needs 1 strep test).

Decision Point F: ESI Level 5 (Non-Urgent)

Definition: The patient requires zero resources (as defined above).

Clinical Criteria: Stable, minor conditions requiring only an exam, oral medications, or basic wound care.

Action: Can safely wait; often treated in a fast-track area.

Keywords for AI: Suture removal, prescription refill, minor rash, poison ivy, healthy child with a mild cold (needs only exam and oral meds).
"""


def main():
    db = SessionLocal()
    try:
        from utils.esi_vector import ingest_esi_protocol
        
        print("Ingesting ESI protocol into vector store...")
        result = ingest_esi_protocol(
            db=db,
            source_text=ESI_PROTOCOL_TEXT,
            source_name="ESI Protocol Overview",
            version="1.0"
        )
        
        print(f"✓ Ingestion complete:")
        print(f"  Document ID: {result['document_id']}")
        print(f"  Source: {result['source']}")
        print(f"  Chunks created: {result['chunks_created']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
