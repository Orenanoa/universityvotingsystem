"""Create demo data: one election, positions, candidates, voters and votes.

Run:  python manage.py seed_demo
Skips anything that already exists, so it is safe to run repeatedly.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from voting.models import Candidate, Election, Position, VoterProfile, Vote

ELECTION = {
    "name": "Student Council 2026",
    "description": "Annual university student council election.",
    "published": True,
}

POSITIONS = [
    ("President", 1, "Head of the student council; chairs all council meetings."),
    ("Vice President", 2, "Deputises the president and oversees student welfare."),
    ("Secretary General", 3, "Keeps council records and communicates with students."),
]

CANDIDATES = {
    "President": [
        ("Amina Yusuf", "Final-year Computer Science student. Focus: digital campus services."),
        ("Brian Otieno", "Third-year Law student. Focus: student welfare and housing."),
        ("Cynthia Mwangi", "Fourth-year Business student. Focus: clubs and sports funding."),
    ],
    "Vice President": [
        ("David Kimani", "Third-year Engineering student. Focus: lab equipment upgrades."),
        ("Esther Njeri", "Second-year Medicine student. Focus: mental health support."),
    ],
    "Secretary General": [
        ("Felix Barasa", "Fourth-year Economics student. Focus: transparent minutes and records."),
        ("Grace Achieng", "Third-year Education student. Focus: communication with students."),
    ],
}

# username, full name, student_id, department, gender, year, verified
VOTERS = [
    ("jmutua", "Joy Mutua", "CS/2026/001", "Computer Science", "Female", 3, True),
    ("kwaweru", "Kevin Waweru", "CS/2026/002", "Computer Science", "Male", 3, True),
    ("nchebet", "Naomi Chebet", "LW/2026/010", "Law", "Female", 2, True),
    ("todhiambo", "Tom Odhiambo", "MD/2026/014", "Medicine", "Male", 4, False),  # not verified: cannot vote
    ("lachieng", "Lucy Achieng", "BS/2026/021", "Business", "Female", 4, True),
    ("pkamau", "Peter Kamau", "EN/2026/033", "Engineering", "Male", 1, True),
]

password = "student123"


class Command(BaseCommand):
    help = "Seed demo election, positions, candidates, voters and votes."

    def handle(self, *args, **options):
        now = timezone.now()

        election, _ = Election.objects.get_or_create(
            name=ELECTION["name"],
            defaults={
                "description": ELECTION["description"],
                "starts_at": now - timedelta(days=1),
                "ends_at": now + timedelta(days=7),
                "published": ELECTION["published"],
            },
        )

        positions = {}
        for title, order, description in POSITIONS:
            pos, _ = Position.objects.get_or_create(
                election=election, title=title,
                defaults={"order": order, "description": description},
            )
            positions[title] = pos
            for name, bio in CANDIDATES[title]:
                Candidate.objects.get_or_create(position=pos, name=name, defaults={"bio": bio})

        # Staff account to manage data through the admin/UI
        if not User.objects.filter(username="staff").exists():
            User.objects.create_user("staff", "staff@uni.ac", password, is_staff=True)

        voters = []
        for username, full_name, sid, dept, gender, year, verified in VOTERS:
            first, _, last = full_name.partition(" ")
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@uni.ac",
                },
            )
            user.set_password(password)
            user.save()
            VoterProfile.objects.get_or_create(
                user=user,
                defaults={
                    "student_id": sid,
                    "department": dept,
                    "gender": gender,
                    "year_of_study": year,
                    "is_verified": verified,
                },
            )
            if verified:
                voters.append(user)

        # Cast sample votes: every verified voter votes for the first
        # candidate of each position, except voter 2 who splits their vote.
        existing = Vote.objects.filter(voter__in=voters, position__election=election).exists()
        if not existing:
            for position in positions.values():
                candidates = list(position.candidates.all())
                if not candidates:
                    continue
                for i, voter in enumerate(voters):
                    candidate = candidates[i % len(candidates)]
                    Vote.objects.create(voter=voter, position=position, candidate=candidate)
            self.stdout.write("Sample votes cast.")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Election '{election.name}' with "
            f"{Position.objects.filter(election=election).count()} positions, "
            f"{Candidate.objects.filter(position__election=election).count()} candidates, "
            f"{len(VOTERS)} voters."
        ))
        self.stdout.write("Logins -> admin/admin123, staff/student123, voters/student123")
