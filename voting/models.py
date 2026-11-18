from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError


class Election(models.Model):
    """A voting event, e.g. 'Student Council 2026'."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    published = models.BooleanField(default=False, help_text="Visible to voters")

    class Meta:
        ordering = ['-starts_at']

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        from django.utils import timezone
        now = timezone.now()
        return self.published and self.starts_at <= now <= self.ends_at


class Position(models.Model):
    """A role being voted on within an election, e.g. 'President'."""

    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ['election', 'title']

    def __str__(self):
        return f"{self.title} — {self.election.name}"


class Candidate(models.Model):
    """A person running for a position."""

    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    student = models.ForeignKey('VoterProfile', on_delete=models.SET_NULL, blank=True, null=True,
                                related_name='candidacies', help_text="The student standing (optional)")
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)

    class Meta:
        ordering = ['position__order', 'name']
        unique_together = ['position', 'name']

    def __str__(self):
        return f"{self.name} ({self.position.title})"

    @property
    def vote_count(self):
        return self.votes.count()


class VoterProfile(models.Model):
    """Extends Django's User with voting eligibility info."""

    YEAR_CHOICES = [
        (1, 'Year 1'), (2, 'Year 2'), (3, 'Year 3'), (4, 'Year 4'),
    ]
    SESSION_CHOICES = [
        ('2024/2025', '2024/2025'),
        ('2025/2026', '2025/2026'),
        ('2026/2027', '2026/2027'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='voter_profile')
    student_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=[('Male', 'Male'), ('Female', 'Female')])
    year_of_study = models.PositiveIntegerField(default=1, choices=YEAR_CHOICES)
    session = models.CharField(max_length=20, default='2025/2026', choices=SESSION_CHOICES)
    is_verified = models.BooleanField(default=False, help_text="Allowed to vote")

    def __str__(self):
        return f"{self.user.username} ({self.student_id})"


class Vote(models.Model):
    """A single ballot choice. One vote per voter per position."""

    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['voter', 'position']

    def __str__(self):
        return self.voter.username + " → " + self.candidate.name

    def clean(self):
        if self.candidate.position_id != self.position_id:
            raise ValidationError("Candidate is not running for this position.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
