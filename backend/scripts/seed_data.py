#!/usr/bin/env python3
"""
backend/scripts/seed_data.py — Seed database with 15 synthetic patients.

Covers all four override cases:
1. No AI (manual entry)
2. AI accepted (both flags false)
3. Fully overridden (both flags true)
4. Partially overridden (one flag true, one false)

Makes dashboard charts visually meaningful on first load.

Usage:
  python scripts/seed_data.py

Or via Docker:
  docker-compose exec backend python scripts/seed_data.py
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base
from app.models.patient import Patient
from app.models.intake import IntakeRecord, UrgencyLevel, Department, TriageSource


# Synthetic patient data covering all override scenarios
SEED_DATA = [
    # =======================================================================
    # Case 1: No AI (triage_source=None, both override flags=None)
    # =======================================================================
    {
        "name": "Rajesh Kumar",
        "age": 45,
        "gender": "Male",
        "contact_number": "9876543210",
        "symptoms_text": "Persistent cough for 3 weeks, mild fever in evenings",
        "triage_source": None,
        "ai_suggested_urgency": None,
        "ai_suggested_department": None,
        "ai_confidence": None,
        "final_urgency": UrgencyLevel.routine,
        "final_department": Department.general_medicine,
        "hours_ago": 2,
    },
    {
        "name": "Priya Sharma",
        "age": 28,
        "gender": "Female",
        "contact_number": "9123456789",
        "symptoms_text": "Skin rash on arms, slightly itchy",
        "triage_source": None,
        "ai_suggested_urgency": None,
        "ai_suggested_department": None,
        "ai_confidence": None,
        "final_urgency": UrgencyLevel.routine,
        "final_department": Department.dermatology,
        "hours_ago": 5,
    },
    {
        "name": "Mohammed Ali",
        "age": 52,
        "gender": "Male",
        "contact_number": "9988776655",
        "symptoms_text": "Lower back pain, difficulty bending",
        "triage_source": None,
        "ai_suggested_urgency": None,
        "ai_suggested_department": None,
        "ai_confidence": None,
        "final_urgency": UrgencyLevel.priority,
        "final_department": Department.orthopedics,
        "hours_ago": 8,
    },
    
    # =======================================================================
    # Case 2: AI Accepted (both override flags=False)
    # =======================================================================
    {
        "name": "Sunita Patel",
        "age": 34,
        "gender": "Female",
        "contact_number": "9876512340",
        "symptoms_text": "Chest pain radiating to left arm, shortness of breath",
        "triage_source": TriageSource.rule_engine,
        "ai_suggested_urgency": UrgencyLevel.urgent,
        "ai_suggested_department": Department.emergency,
        "ai_confidence": None,  # Rule engine has no confidence
        "final_urgency": UrgencyLevel.urgent,
        "final_department": Department.emergency,
        "hours_ago": 1,
    },
    {
        "name": "Amit Deshmukh",
        "age": 67,
        "gender": "Male",
        "contact_number": "9123498765",
        "symptoms_text": "Palpitations and dizziness for past 2 hours",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.priority,
        "ai_suggested_department": Department.cardiology,
        "ai_confidence": 0.87,
        "final_urgency": UrgencyLevel.priority,
        "final_department": Department.cardiology,
        "hours_ago": 3,
    },
    {
        "name": "Kavita Reddy",
        "age": 41,
        "gender": "Female",
        "contact_number": "9988112233",
        "symptoms_text": "Severe migraine with visual aura",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.priority,
        "ai_suggested_department": Department.neurology,
        "ai_confidence": 0.92,
        "final_urgency": UrgencyLevel.priority,
        "final_department": Department.neurology,
        "hours_ago": 6,
    },
    {
        "name": "Ravi Gupta",
        "age": 29,
        "gender": "Male",
        "contact_number": "9876543211",
        "symptoms_text": "High fever, body ache, fatigue",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.routine,
        "ai_suggested_department": Department.general_medicine,
        "ai_confidence": 0.78,
        "final_urgency": UrgencyLevel.routine,
        "final_department": Department.general_medicine,
        "hours_ago": 12,
    },
    
    # =======================================================================
    # Case 3: Fully Overridden (both override flags=True)
    # =======================================================================
    {
        "name": "Deepak Singh",
        "age": 55,
        "gender": "Male",
        "contact_number": "9123450987",
        "symptoms_text": "Mild abdominal discomfort, bloating",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.routine,
        "ai_suggested_department": Department.general_medicine,
        "ai_confidence": 0.65,
        "final_urgency": UrgencyLevel.urgent,  # Receptionist upgraded
        "final_department": Department.emergency,  # Receptionist changed
        "hours_ago": 4,
    },
    {
        "name": "Meera Iyer",
        "age": 38,
        "gender": "Female",
        "contact_number": "9988771122",
        "symptoms_text": "Joint pain in knees, occasional swelling",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.routine,
        "ai_suggested_department": Department.orthopedics,
        "ai_confidence": 0.72,
        "final_urgency": UrgencyLevel.priority,  # Receptionist upgraded
        "final_department": Department.rheumatology if hasattr(Department, 'rheumatology') else Department.general_medicine,
        "hours_ago": 7,
    },
    {
        "name": "Arun Kapoor",
        "age": 62,
        "gender": "Male",
        "contact_number": "9876501234",
        "symptoms_text": "Intermittent chest tightness, mild shortness of breath",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.priority,
        "ai_suggested_department": Department.pulmonology,
        "ai_confidence": 0.58,
        "final_urgency": UrgencyLevel.urgent,  # Receptionist upgraded
        "final_department": Department.cardiology,  # Receptionist changed
        "hours_ago": 9,
    },
    
    # =======================================================================
    # Case 4: Partially Overridden (one flag=True, one=False)
    # =======================================================================
    {
        "name": "Pooja Malhotra",
        "age": 31,
        "gender": "Female",
        "contact_number": "9123409876",
        "symptoms_text": "Persistent headache, sensitivity to light",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.routine,
        "ai_suggested_department": Department.general_medicine,
        "ai_confidence": 0.55,
        "final_urgency": UrgencyLevel.priority,  # Urgency overridden
        "final_department": Department.general_medicine,  # Department accepted
        "hours_ago": 10,
    },
    {
        "name": "Sanjay Verma",
        "age": 48,
        "gender": "Male",
        "contact_number": "9988665544",
        "symptoms_text": "Numbness in left hand, occasional dizziness",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.priority,
        "ai_suggested_department": Department.neurology,
        "ai_confidence": 0.81,
        "final_urgency": UrgencyLevel.priority,  # Urgency accepted
        "final_department": Department.cardiology,  # Department overridden
        "hours_ago": 11,
    },
    {
        "name": "Anita Joshi",
        "age": 26,
        "gender": "Female",
        "contact_number": "9876512341",
        "symptoms_text": "Ear pain, mild hearing loss in right ear",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.priority,
        "ai_suggested_department": Department.ent,
        "ai_confidence": 0.89,
        "final_urgency": UrgencyLevel.routine,  # Urgency downgraded
        "final_department": Department.ent,  # Department accepted
        "hours_ago": 14,
    },
    {
        "name": "Vikram Rao",
        "age": 59,
        "gender": "Male",
        "contact_number": "9123456780",
        "symptoms_text": "Chronic cough, wheezing, history of asthma",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.routine,
        "ai_suggested_department": Department.pulmonology,
        "ai_confidence": 0.94,
        "final_urgency": UrgencyLevel.routine,  # Urgency accepted
        "final_department": Department.pulmonology,  # Department accepted (AI accepted case)
        "hours_ago": 18,
    },
    {
        "name": "Lakshmi Narayan",
        "age": 73,
        "gender": "Female",
        "contact_number": "9988112244",
        "symptoms_text": "Abdominal pain, nausea, loss of appetite",
        "triage_source": TriageSource.llm,
        "ai_suggested_urgency": UrgencyLevel.priority,
        "ai_suggested_department": Department.gastroenterology,
        "ai_confidence": 0.76,
        "final_urgency": UrgencyLevel.priority,  # Urgency accepted
        "final_department": Department.gastroenterology,  # Department accepted
        "hours_ago": 22,
    },
]


async def seed_database():
    """Seed the database with synthetic patient data."""
    
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/patient_intake"
    )
    
    print(f"Connecting to database: {database_url.split('@')[1].split('/')[0]}")
    
    # Create async engine and session
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with session_factory() as session:
            now = datetime.now(timezone.utc)
            
            print(f"\n📊 Seeding {len(SEED_DATA)} synthetic patients...")
            print("-" * 60)
            
            for i, data in enumerate(SEED_DATA, 1):
                hours_ago = data.pop("hours_ago")
                created_at = now - timedelta(hours=hours_ago)
                
                # Create patient
                patient = Patient(
                    name=data["name"],
                    age=data["age"],
                    gender=data["gender"],
                    contact_number=data["contact_number"],
                )
                session.add(patient)
                await session.flush()  # Get patient.id
                
                # Create intake record
                record = IntakeRecord(
                    patient_id=patient.id,
                    symptoms_text=data["symptoms_text"],
                    triage_source=data["triage_source"],
                    ai_suggested_urgency=data["ai_suggested_urgency"],
                    ai_suggested_department=data["ai_suggested_department"],
                    ai_confidence=data["ai_confidence"],
                    final_urgency=data["final_urgency"],
                    final_department=data["final_department"],
                    created_at=created_at,
                )
                session.add(record)
                
                # Compute override flags
                if data["triage_source"] is None:
                    urgency_overridden = None
                    department_overridden = None
                else:
                    urgency_overridden = data["final_urgency"] != data["ai_suggested_urgency"]
                    department_overridden = data["final_department"] != data["ai_suggested_department"]
                
                record.urgency_overridden = urgency_overridden
                record.department_overridden = department_overridden
                
                # Status emoji
                if data["triage_source"] is None:
                    status = "📝 Manual"
                elif not urgency_overridden and not department_overridden:
                    status = "✅ AI Accepted"
                elif urgency_overridden and department_overridden:
                    status = "⚠️  Fully Overridden"
                else:
                    status = "🔶 Partially Overridden"
                
                print(f"{i:2d}. {data['name']:20s} → {data['final_urgency'].value:10s} {data['final_department'].value:20s} [{status}]")
                
                # Restore hours_ago for next iteration
                data["hours_ago"] = hours_ago
            
            await session.commit()
            
            # Print summary
            print("-" * 60)
            print(f"✅ Successfully seeded {len(SEED_DATA)} patients")
            
            # Print dashboard-like summary
            urgency_counts = {}
            dept_counts = {}
            source_counts = {"Manual": 0, "AI Accepted": 0, "Overridden": 0}
            
            for data in SEED_DATA:
                # Urgency
                u = data["final_urgency"].value
                urgency_counts[u] = urgency_counts.get(u, 0) + 1
                
                # Department
                d = data["final_department"].value
                dept_counts[d] = dept_counts.get(d, 0) + 1
                
                # Source
                if data["triage_source"] is None:
                    source_counts["Manual"] += 1
                elif data["triage_source"] in [TriageSource.llm, TriageSource.rule_engine]:
                    if data["final_urgency"] == data["ai_suggested_urgency"] and \
                       data["final_department"] == data["ai_suggested_department"]:
                        source_counts["AI Accepted"] += 1
                    else:
                        source_counts["Overridden"] += 1
            
            print("\n📈 Dashboard Summary:")
            print("  By Urgency:")
            for urgency, count in sorted(urgency_counts.items()):
                bar = "█" * count
                print(f"    {urgency:10s}: {bar} ({count})")
            
            print("  By Source:")
            for source, count in source_counts.items():
                bar = "█" * count
                print(f"    {source:15s}: {bar} ({count})")
            
            print("\n💡 Dashboard will now show meaningful charts and statistics!")
            
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("🌱 Patient Intake System — Seed Data Script")
    print("=" * 60)
    asyncio.run(seed_database())