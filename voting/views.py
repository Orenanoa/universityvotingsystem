from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ElectionForm, PositionForm, CandidateForm, VoterProfileForm,
    StyledAuthenticationForm, BallotForm,
)
from .models import Election, Position, Candidate, VoterProfile, Vote


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


# ---------- Public / voter views ----------

def home(request):
    elections = Election.objects.filter(published=True)
    now = timezone.now()
    open_elections = [e for e in elections if e.starts_at <= now <= e.ends_at]
    upcoming = [e for e in elections if e.starts_at > now]
    closed = [e for e in elections if e.ends_at < now]
    return render(request, 'home.html', {
        'open_elections': open_elections,
        'upcoming': upcoming,
        'closed': closed,
    })


def elections_list(request):
    elections = Election.objects.filter(published=True).annotate(
        n_positions=Count('positions', distinct=True),
        n_candidates=Count('positions__candidates', distinct=True),
    )
    return render(request, 'elections.html', {'elections': elections})


def election_detail(request, pk):
    election = get_object_or_404(Election, pk=pk, published=True)
    return render(request, 'election.html', {'election': election})


@login_required
def ballot(request, pk):
    election = get_object_or_404(Election, pk=pk, published=True)
    if not election.is_open:
        messages.error(request, 'This election is not open for voting right now.')
        return redirect('election_detail', pk=election.pk)

    if request.method == 'POST':
        form = BallotForm(request.POST, election=election, voter=request.user)
        if form.is_valid():
            for position in form.positions:
                candidate = form.cleaned_data[f'position_{position.pk}']
                if candidate:
                    Vote.objects.update_or_create(
                        voter=request.user, position=position,
                        defaults={'candidate': candidate},
                    )
            messages.success(request, 'Your ballot has been recorded. Thank you for voting!')
            return redirect('results', pk=election.pk)
    else:
        form = BallotForm(election=election, voter=request.user)

    # Pre-select the voter's existing choices
    existing = {v.position_id: v.candidate_id for v in
                Vote.objects.filter(voter=request.user, position__election=election)}
    for position in form.positions:
        initial_id = existing.get(position.pk)
        if initial_id:
            form.fields[f'position_{position.pk}'].initial = initial_id

    return render(request, 'ballot.html', {'election': election, 'form': form})


@login_required
def results(request, pk):
    election = get_object_or_404(Election, pk=pk)
    positions = election.positions.all().prefetch_related('candidates')
    for position in positions:
        candidates = list(position.candidates.annotate(n_votes=Count('votes')))
        candidates.sort(key=lambda c: -c.n_votes)
        position.results = candidates
        position.total_votes = sum(c.n_votes for c in candidates)
    return render(request, 'election.html', {
        'election': election, 'results_mode': True, 'positions': positions,
    })


# ---------- Authentication ----------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f'Welcome back, {request.user.username}!')
            next_url = request.GET.get('next') or 'home'
            return redirect(next_url)
    else:
        form = StyledAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ---------- Staff CRUD: elections ----------

@staff_required
def manage_elections(request):
    elections = Election.objects.annotate(
        n_positions=Count('positions', distinct=True),
    )
    return render(request, 'crud/list.html', {
        'title': 'Elections',
        'object_list': elections,
        'create_url': 'election_create',
        'update_url': 'election_update',
        'delete_url': 'election_delete',
        'fields': ['name', 'starts_at', 'ends_at', 'published', 'n_positions'],
    })


@staff_required
def election_create(request):
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Election created.')
            return redirect('manage_elections')
    else:
        form = ElectionForm()
    return render(request, 'crud/form.html', {'form': form, 'title': 'New election'})


@staff_required
def election_update(request, pk):
    election = get_object_or_404(Election, pk=pk)
    if request.method == 'POST':
        form = ElectionForm(request.POST, instance=election)
        if form.is_valid():
            form.save()
            messages.success(request, 'Election updated.')
            return redirect('manage_elections')
    else:
        form = ElectionForm(instance=election)
    return render(request, 'crud/form.html', {
        'form': form, 'title': f'Edit: {election.name}',
    })


@staff_required
@require_POST
def election_delete(request, pk):
    get_object_or_404(Election, pk=pk).delete()
    messages.info(request, 'Election deleted.')
    return redirect('manage_elections')


# ---------- Staff CRUD: positions ----------

@staff_required
def position_create(request, election_pk):
    election = get_object_or_404(Election, pk=election_pk)
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            position = form.save(commit=False)
            position.election = election
            position.save()
            messages.success(request, 'Position added.')
            return redirect('manage_positions', election_pk=election.pk)
    else:
        form = PositionForm(initial={'election': election})
    return render(request, 'crud/form.html', {
        'form': form, 'title': f'Add position to {election.name}',
    })


@staff_required
def manage_positions(request, election_pk):
    election = get_object_or_404(Election, pk=election_pk)
    return render(request, 'crud/positions.html', {'election': election})


@staff_required
def position_update(request, pk):
    position = get_object_or_404(Position, pk=pk)
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, 'Position updated.')
            return redirect('manage_positions', election_pk=position.election.pk)
    else:
        form = PositionForm(instance=position)
    return render(request, 'crud/form.html', {'form': form, 'title': f'Edit: {position.title}'})


@staff_required
@require_POST
def position_delete(request, pk):
    position = get_object_or_404(Position, pk=pk)
    election_pk = position.election.pk
    position.delete()
    messages.info(request, 'Position deleted.')
    return redirect('manage_positions', election_pk=election_pk)


# ---------- Staff CRUD: candidates ----------

@staff_required
def candidate_create(request, position_pk):
    position = get_object_or_404(Position, pk=position_pk)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.position = position
            candidate.save()
            messages.success(request, 'Candidate added.')
            return redirect('manage_positions', election_pk=position.election.pk)
    else:
        form = CandidateForm(initial={'position': position})
    return render(request, 'crud/form.html', {
        'form': form, 'title': f'Add candidate to {position.title}', 'enctype': True,
    })


@staff_required
def candidate_update(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidate updated.')
            return redirect('manage_positions', election_pk=candidate.position.election.pk)
    else:
        form = CandidateForm(instance=candidate)
    return render(request, 'crud/form.html', {
        'form': form, 'title': f'Edit candidate: {candidate.name}', 'enctype': True,
    })


@staff_required
@require_POST
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    election_pk = candidate.position.election.pk
    candidate.delete()
    messages.info(request, 'Candidate deleted.')
    return redirect('manage_positions', election_pk=election_pk)


# ---------- Staff CRUD: voters ----------

@staff_required
def manage_voters(request):
    profiles = VoterProfile.objects.select_related('user').all()
    return render(request, 'students.html', {'profiles': profiles})


@staff_required
def voter_create(request):
    if request.method == 'POST':
        form = VoterProfileForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, 'Voter account created.')
            return redirect('manage_voters')
    else:
        form = VoterProfileForm()
    return render(request, 'crud/form.html', {'form': form, 'title': 'New voter'})


@staff_required
def voter_update(request, pk):
    profile = get_object_or_404(VoterProfile, pk=pk)
    if request.method == 'POST':
        form = VoterProfileForm(request.POST, instance=profile)
        # Username/password are optional on edit
        form.fields['username'].required = False
        form.fields['password'].required = False
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if username and username != profile.user.username:
                if User.objects.filter(username=username).exclude(pk=profile.user.pk).exists():
                    form.add_error('username', 'This username is already taken.')
                    return render(request, 'crud/form.html', {
                        'form': form, 'title': f'Edit voter: {profile.user.username}',
                    })
                profile.user.username = username
            if password:
                profile.user.set_password(password)
            profile.user.save()
            profile = form.save(commit=False)
            profile.user.save()
            profile.save()
            messages.success(request, 'Voter updated.')
            return redirect('manage_voters')
    else:
        form = VoterProfileForm(instance=profile, initial={'username': profile.user.username})
        form.fields['username'].required = False
        form.fields['password'].required = False
    return render(request, 'crud/form.html', {
        'form': form, 'title': f'Edit voter: {profile.user.username}',
    })


@staff_required
@require_POST
def voter_delete(request, pk):
    profile = get_object_or_404(VoterProfile, pk=pk)
    profile.user.delete()  # deletes profile too (cascade)
    messages.info(request, 'Voter deleted.')
    return redirect('manage_voters')


@staff_required
@require_POST
def voter_toggle_verify(request, pk):
    profile = get_object_or_404(VoterProfile, pk=pk)
    profile.is_verified = not profile.is_verified
    profile.save()
    messages.success(request, f"{profile.user.username} is {'now verified' if profile.is_verified else 'no longer verified'}.")
    return redirect('manage_voters')
