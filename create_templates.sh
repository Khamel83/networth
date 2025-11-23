#!/bin/bash
# Script to create all NET WORTH templates

echo "Creating all templates..."

# Create dashboard.html
cat > /home/user/networth/templates/dashboard.html << 'EOF'
{% extends "base.html" %}
{% block title %}Dashboard - NET WORTH{% endblock %}
{% block content %}
<h1 style="margin-bottom: 2rem;">Welcome, {{ player.name }}!</h1>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
    <div class="card" style="background: var(--gradient); color: white;">
        <h3>Rank</h3>
        <p style="font-size: 2.5rem; font-weight: 700;">#{{ rank }}</p>
        <p style="opacity: 0.9;">of {{ total_players}} players</p>
    </div>
    <div class="card">
        <h3>Record</h3>
        <p style="font-size: 2rem; font-weight: 700;">{{ player.wins }}-{{ player.losses }}</p>
        <p>Win Rate: {{ "%.1f"|format(win_rate) }}%</p>
    </div>
    <div class="card">
        <h3>Score</h3>
        <p style="font-size: 2rem; font-weight: 700;">{{ player.total_score }}</p>
        <p>Skill: {{ player.skill_level }}</p>
    </div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
    <div class="card">
        <h2>Recent Matches</h2>
        {% if recent_matches %}
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Opponent</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {% for match in recent_matches %}
                <tr>
                    <td>{{ match.match_date }}</td>
                    <td>{% if match.player1_id == session.player_id %}{{ match.player2_name }}{% else %}{{ match.player1_name }}{% endif %}</td>
                    <td>{{ match.player1_set1 }}-{{ match.player2_set1 }}, {{ match.player1_set2 }}-{{ match.player2_set2 }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>No matches yet.</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>Quick Actions</h2>
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <a href="/report-score" class="btn btn-primary"><i class="fas fa-plus"></i> Report Score</a>
            <a href="/history" class="btn btn-secondary"><i class="fas fa-history"></i> View Full History</a>
        </div>
        {% if pending_matches %}
        <h3 style="margin-top: 2rem;">Pending Scores ({{ pending_matches|length }})</h3>
        <p style="color: var(--warning);">You have {{ pending_matches|length }} match(es) awaiting admin review.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
EOF

# Create report_score.html
cat > /home/user/networth/templates/report_score.html << 'EOF'
{% extends "base.html" %}
{% block title %}Report Score - NET WORTH{% endblock %}
{% block content %}
<div class="card" style="max-width: 600px; margin: 0 auto;">
    <h2><i class="fas fa-trophy"></i> Report Match Score</h2>
    <form method="POST" action="/report-score">
        <div class="form-group">
            <label for="opponent_id">Opponent *</label>
            <select class="form-control" id="opponent_id" name="opponent_id" required>
                <option value="">Select opponent...</option>
                {% for p in players %}
                <option value="{{ p.id }}">{{ p.name }} ({{ p.skill_level }})</option>
                {% endfor %}
            </select>
        </div>

        <div class="form-group">
            <label for="match_date">Match Date *</label>
            <input type="date" class="form-control" id="match_date" name="match_date" value="{{ today }}" max="{{ today }}" required>
        </div>

        <h3 style="margin-top: 2rem;">Set Scores</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
                <label>Your Set 1</label>
                <input type="number" class="form-control" name="player_set1" min="0" max="7" required>
            </div>
            <div class="form-group">
                <label>Opponent Set 1</label>
                <input type="number" class="form-control" name="opponent_set1" min="0" max="7" required>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
                <label>Your Set 2</label>
                <input type="number" class="form-control" name="player_set2" min="0" max="7" required>
            </div>
            <div class="form-group">
                <label>Opponent Set 2</label>
                <input type="number" class="form-control" name="opponent_set2" min="0" max="7" required>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
                <label>Your Set 3 (if played)</label>
                <input type="number" class="form-control" name="player_set3" min="0" max="7">
            </div>
            <div class="form-group">
                <label>Opponent Set 3 (if played)</label>
                <input type="number" class="form-control" name="opponent_set3" min="0" max="7">
            </div>
        </div>

        <div class="form-group">
            <label for="notes">Notes (optional)</label>
            <textarea class="form-control" id="notes" name="notes" rows="3"></textarea>
        </div>

        <div style="display: flex; gap: 1rem;">
            <a href="/dashboard" class="btn btn-secondary">Cancel</a>
            <button type="submit" class="btn btn-primary">Submit Score</button>
        </div>
    </form>
</div>

<script>
document.querySelector('form').addEventListener('submit', function(e) {
    var date = new Date(document.getElementById('match_date').value);
    if (!date || date > new Date()) {
        e.preventDefault();
        alert('Please enter a valid match date (not in the future).');
    }
});
</script>
{% endblock %}
EOF

# Create history.html
cat > /home/user/networth/templates/history.html << 'EOF'
{% extends "base.html" %}
{% block title %}Match History - NET WORTH{% endblock %}
{% block content %}
<div class="card">
    <h2><i class="fas fa-history"></i> Match History</h2>
    {% if matches %}
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Opponent</th>
                <th>Score</th>
                <th>Result</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for match in matches %}
            <tr>
                <td>{{ match.match_date }}</td>
                <td>{{ match.opponent_name }}</td>
                <td>{{ match.player1_set1 }}-{{ match.player2_set1 }}, {{ match.player1_set2 }}-{{ match.player2_set2 }}{% if match.player1_set3 %}, {{ match.player1_set3 }}-{{ match.player2_set3 }}{% endif %}</td>
                <td><strong>{{ match.result }}</strong></td>
                <td>
                    {% if match.status == 'confirmed' %}
                    <span style="color: var(--secondary);"><i class="fas fa-check-circle"></i> Confirmed</span>
                    {% elif match.status == 'pending' %}
                    <span style="color: var(--warning);"><i class="fas fa-clock"></i> Pending</span>
                    {% else %}
                    <span style="color: var(--danger);"><i class="fas fa-times-circle"></i> {{ match.status }}</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>No matches yet. <a href="/report-score">Report your first match!</a></p>
    {% endif %}
</div>
{% endblock %}
EOF

echo "Player templates created!"

# Create admin templates
cat > /home/user/networth/templates/admin_dashboard.html << 'EOF'
{% extends "base.html" %}
{% block title %}Admin Dashboard - NET WORTH{% endblock %}
{% block content %}
<h1><i class="fas fa-shield-alt"></i> Admin Dashboard</h1>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin: 2rem 0;">
    <div class="card" style="background: var(--info); color: white;">
        <h3>Total Players</h3>
        <p style="font-size: 3rem; font-weight: 700;">{{ total_players }}</p>
    </div>
    <div class="card" style="background: var(--warning); color: white;">
        <h3>Pending Scores</h3>
        <p style="font-size: 3rem; font-weight: 700;">{{ pending_scores }}</p>
    </div>
    <div class="card" style="background: var(--secondary); color: white;">
        <h3>Confirmed Matches</h3>
        <p style="font-size: 3rem; font-weight: 700;">{{ confirmed_matches }}</p>
    </div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
    <div class="card">
        <h2>Quick Actions</h2>
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <a href="/admin/players/add" class="btn btn-primary"><i class="fas fa-user-plus"></i> Add Player</a>
            <a href="/admin/scores" class="btn btn-warning"><i class="fas fa-clipboard-check"></i> Review Scores ({{ pending_scores }})</a>
            <a href="/admin/players" class="btn btn-secondary"><i class="fas fa-users"></i> Manage Players</a>
        </div>
    </div>

    <div class="card">
        <h2>Recent Activity</h2>
        {% if recent_activity %}
        <ul style="list-style: none;">
            {% for activity in recent_activity[:5] %}
            <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--light-gray);">
                <small>{{ activity.created_at[:10] }}</small><br>
                {{ activity.player1_name }} vs {{ activity.player2_name }}
                <span style="color: var(--{% if activity.status == 'confirmed' %}secondary{% else %}warning{% endif %});">• {{ activity.status }}</span>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p>No recent activity.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
EOF

cat > /home/user/networth/templates/admin_players.html << 'EOF'
{% extends "base.html" %}
{% block title %}Manage Players - NET WORTH Admin{% endblock %}
{% block content %}
<h1><i class="fas fa-users"></i> Manage Players</h1>

<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <form method="GET" style="flex: 1; max-width: 500px; display: flex; gap: 1rem;">
            <input type="text" class="form-control" name="search" placeholder="Search by name or email..." value="{{ search }}">
            <button type="submit" class="btn btn-primary">Search</button>
        </form>
        <a href="/admin/players/add" class="btn btn-success"><i class="fas fa-plus"></i> Add Player</a>
    </div>

    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Name</th>
                <th>Email</th>
                <th>Skill</th>
                <th>Record</th>
                <th>Score</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for player in players %}
            <tr>
                <td>#{{ player.rank }}</td>
                <td>{{ player.name }}</td>
                <td>{{ player.email }}</td>
                <td>{{ player.skill_level }}</td>
                <td>{{ player.wins }}-{{ player.losses }}</td>
                <td>{{ player.total_score }}</td>
                <td>
                    <a href="/admin/players/edit/{{ player.id }}" class="btn btn-secondary" style="padding: 0.5rem 1rem;">Edit</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
EOF

cat > /home/user/networth/templates/admin_add_player.html << 'EOF'
{% extends "base.html" %}
{% block title %}Add Player - NET WORTH Admin{% endblock %}
{% block content %}
<div class="card" style="max-width: 600px; margin: 0 auto;">
    <h2><i class="fas fa-user-plus"></i> Add New Player</h2>
    <form method="POST">
        <div class="form-group">
            <label for="name">Name *</label>
            <input type="text" class="form-control" id="name" name="name" value="{{ name or '' }}" required>
        </div>
        <div class="form-group">
            <label for="email">Email *</label>
            <input type="email" class="form-control" id="email" name="email" value="{{ email or '' }}" required>
        </div>
        <div class="form-group">
            <label for="skill_level">Skill Level (NTRP) *</label>
            <select class="form-control" id="skill_level" name="skill_level">
                <option value="2.5">2.5</option>
                <option value="3.0">3.0</option>
                <option value="3.5" selected>3.5</option>
                <option value="4.0">4.0</option>
                <option value="4.5">4.5</option>
                <option value="5.0">5.0</option>
            </select>
        </div>
        <div style="display: flex; gap: 1rem;">
            <a href="/admin/players" class="btn btn-secondary">Cancel</a>
            <button type="submit" class="btn btn-primary">Add Player</button>
        </div>
    </form>
</div>
{% endblock %}
EOF

cat > /home/user/networth/templates/admin_edit_player.html << 'EOF'
{% extends "base.html" %}
{% block title %}Edit Player - NET WORTH Admin{% endblock %}
{% block content %}
<div class="card" style="max-width: 600px; margin: 0 auto;">
    <h2><i class="fas fa-user-edit"></i> Edit Player</h2>
    <form method="POST">
        <div class="form-group">
            <label for="name">Name *</label>
            <input type="text" class="form-control" id="name" name="name" value="{{ player.name }}" required>
        </div>
        <div class="form-group">
            <label for="email">Email *</label>
            <input type="email" class="form-control" id="email" name="email" value="{{ player.email }}" required>
        </div>
        <div class="form-group">
            <label for="skill_level">Skill Level (NTRP) *</label>
            <select class="form-control" id="skill_level" name="skill_level">
                {% for level in [2.5, 3.0, 3.5, 4.0, 4.5, 5.0] %}
                <option value="{{ level }}" {% if player.skill_level == level %}selected{% endif %}>{{ level }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="is_active">Status *</label>
            <select class="form-control" id="is_active" name="is_active">
                <option value="1" {% if player.is_active %}selected{% endif %}>Active</option>
                <option value="0" {% if not player.is_active %}selected{% endif %}>Inactive</option>
            </select>
        </div>
        <div style="display: flex; gap: 1rem;">
            <a href="/admin/players" class="btn btn-secondary">Cancel</a>
            <button type="submit" class="btn btn-primary">Update Player</button>
        </div>
    </form>
</div>
{% endblock %}
EOF

cat > /home/user/networth/templates/admin_scores.html << 'EOF'
{% extends "base.html" %}
{% block title %}Review Scores - NET WORTH Admin{% endblock %}
{% block content %}
<h1><i class="fas fa-clipboard-check"></i> Review Pending Scores</h1>

<div class="card">
    {% if pending_scores %}
    {% for score in pending_scores %}
    <div style="padding: 1.5rem; margin-bottom: 1.5rem; border: 2px solid var(--warning); border-radius: 12px; background: #fffbf0;">
        <h3>{{ score.player1_name }} vs {{ score.player2_name }}</h3>
        <p><strong>Date:</strong> {{ score.match_date }}</p>
        <p><strong>Reported by:</strong> {{ score.reporter_name }}</p>
        <p><strong>Score:</strong> {{ score.player1_set1 }}-{{ score.player2_set1 }}, {{ score.player1_set2 }}-{{ score.player2_set2 }}</p>
        <p><strong>Winner:</strong> {% if score.player1_total > score.player2_total %}{{ score.player1_name }}{% else %}{{ score.player2_name }}{% endif %}</p>
        {% if score.notes %}
        <p><strong>Notes:</strong> {{ score.notes }}</p>
        {% endif %}
        <div style="display: flex; gap: 1rem; margin-top: 1rem;">
            <form method="POST" action="/admin/scores/approve/{{ score.id }}" style="display: inline;">
                <button type="submit" class="btn btn-success">✓ Approve</button>
            </form>
            <form method="POST" action="/admin/scores/reject/{{ score.id }}" style="display: inline;">
                <button type="submit" class="btn btn-danger">✗ Reject</button>
            </form>
        </div>
    </div>
    {% endfor %}
    {% else %}
    <p>No pending scores to review.</p>
    {% endif %}
</div>
{% endblock %}
EOF

echo "All admin templates created!"
echo "✓ Template creation complete!"
