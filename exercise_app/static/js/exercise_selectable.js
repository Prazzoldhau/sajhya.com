// static/js/exercise_selectable.js

// Helper Functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getDifficultyText(level) {
    const levels = {
        1: 'Beginner',
        2: 'Intermediate',
        3: 'Advanced',
        4: 'Super Level'
    };
    return levels[level] || `Level ${level}`;
}

function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    const subRegionSelect = document.getElementById('subRegionSelect');
    const exercisesContainer = document.getElementById('exercisesContainer');
    const loader = document.getElementById('loader');
    const stats = document.getElementById('stats');
    const prescribeBtn = document.getElementById('prescribeBtn');
    
    if (!subRegionSelect || !exercisesContainer) {
        console.error('Required elements not found');
        return;
    }
    
    // Track visible count per difficulty level
    window.visibleCount = {
        1: 3, 2: 3, 3: 3, 4: 3, 5: 3
    };
    
    // Store grouped exercises for each difficulty
    window.groupedExercises = {
        1: [], 2: [], 3: [], 4: []
    };
    
    const INITIAL_COUNT = 4;
    const LOAD_MORE_COUNT = 5;
    
    subRegionSelect.addEventListener('change', function() {
        const subRegionId = this.value;
        if (!subRegionId) {
            showEmptyState('No exercises selected', 'Please select a sub-region to view exercises');
            if (stats) stats.classList.remove('show');
            return;
        }
        fetchExercises(subRegionId);
    });
    
    if (prescribeBtn) {
        prescribeBtn.addEventListener('click', openPrescriptionModal);
    }
    
    async function fetchExercises(subRegionId) {
        if (loader) loader.style.display = 'block';
        if (exercisesContainer) exercisesContainer.innerHTML = '';
        if (stats) stats.classList.remove('show');
        
        window.selectedExercises = [];
        updateSelectionSummary();
        
        // Reset visible counts
        window.visibleCount = {1: INITIAL_COUNT, 2: INITIAL_COUNT, 3: INITIAL_COUNT, 4: INITIAL_COUNT, 5: INITIAL_COUNT};
        
        try {
            let response;
            try {
                response = await fetch(`/exercise-app/api/get-exercises/?sub_region_id=${subRegionId}`);
            } catch (e) {
                response = await fetch(`/exercise-app/api/get-exercises/?sub_region_id=${subRegionId}`);
            }
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (loader) loader.style.display = 'none';
            
            if (data.success === false) {
                showErrorState(data.error || 'Failed to load exercises');
            } else if (data.exercises && data.exercises.length > 0) {
                window.currentExercises = data.exercises.sort((a, b) => {
                    return (a.difficulty_level || 1) - (b.difficulty_level || 1);
                });
                
                // Group exercises by difficulty
                window.groupedExercises = {
                    1: window.currentExercises.filter(ex => (ex.difficulty_level || 1) === 1),
                    2: window.currentExercises.filter(ex => ex.difficulty_level === 2),
                    3: window.currentExercises.filter(ex => ex.difficulty_level === 3),
                    4: window.currentExercises.filter(ex => ex.difficulty_level === 4),
                    5: window.currentExercises.filter(ex => ex.difficulty_level === 5)
                };
                
                displayExercisesStructure();
                updateStats(data.exercises.length);
            } else {
                showEmptyState('No exercises found', 'No exercises available for this sub-region');
            }
        } catch (error) {
            console.error('Error fetching exercises:', error);
            if (loader) loader.style.display = 'none';
            showErrorState(`Failed to load exercises: ${error.message}`);
        }
    }
    
    function displayExercisesStructure() {
        let html = '';
        
        for (let level = 1; level <= 5; level++) {
            const levelExercises = window.groupedExercises[level];
            if (levelExercises.length === 0) continue;
            
            const visibleCount = window.visibleCount[level];
            const visibleExercises = levelExercises.slice(0, visibleCount);
            const hasMore = levelExercises.length > visibleCount;
            
            html += `
                <div class="difficulty-section" data-difficulty="${level}" id="difficulty-section-${level}">
                    <div class="difficulty-header" style="background: linear-gradient(135deg, ${getDifficultyColor(level)} 0%, ${getDifficultyColor(level)}CC 100%);">
                        <div class="difficulty-title">
                            <span class="difficulty-icon">${getDifficultyIcon(level)}</span>
                            <h2>${getDifficultyText(level)}</h2>
                            <span class="exercise-count">(${levelExercises.length} exercises)</span>
                        </div>
                    </div>
                    <div class="exercises-grid" id="difficulty-grid-${level}">
                        ${visibleExercises.map(exercise => renderExerciseCard(exercise)).join('')}
                    </div>
                    <div class="view-more-container" id="view-more-container-${level}">
                        ${hasMore ? `
                            <button class="view-more-btn" onclick="window.loadMoreExercises(${level})">
                                Load More (${Math.min(levelExercises.length - visibleCount, LOAD_MORE_COUNT)} of ${levelExercises.length - visibleCount} remaining) ▼
                            </button>
                        ` : visibleCount > INITIAL_COUNT ? `
                            <button class="view-less-btn" onclick="window.showLessExercises(${level})">
                                Show Less ▲
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        exercisesContainer.innerHTML = html;
        highlightSelectedExercises();
    }
    
    function renderExerciseCard(exercise) {
        return `
            <div class="exercise-card" data-exercise-id="${exercise.id}" onclick="window.toggleExerciseSelection(${exercise.id})">
                <div class="card-content">
                    <div class="exercise-name">${escapeHtml(exercise.exercise_name || 'Unknown')}</div>
                    <div class="difficulty-badge difficulty-${exercise.difficulty_level || 1}">
                        ${getDifficultyText(exercise.difficulty_level || 1)}
                    </div>
                </div>
            </div>
        `;
    }
    
    function loadMoreExercises(difficultyLevel) {
        const levelExercises = window.groupedExercises[difficultyLevel];
        const currentVisible = window.visibleCount[difficultyLevel];
        const newVisible = Math.min(currentVisible + LOAD_MORE_COUNT, levelExercises.length);
        
        // Get the new exercises to append
        const newExercises = levelExercises.slice(currentVisible, newVisible);
        
        // Update visible count
        window.visibleCount[difficultyLevel] = newVisible;
        
        // Append new exercises to the grid
        const grid = document.getElementById(`difficulty-grid-${difficultyLevel}`);
        if (grid) {
            newExercises.forEach(exercise => {
                const card = document.createElement('div');
                card.innerHTML = renderExerciseCard(exercise);
                grid.appendChild(card.firstElementChild);
            });
            highlightSelectedExercises();
        }
        
        // Update the button
        const hasMore = levelExercises.length > newVisible;
        const container = document.getElementById(`view-more-container-${difficultyLevel}`);
        
        if (container) {
            if (hasMore) {
                const remaining = levelExercises.length - newVisible;
                container.innerHTML = `
                    <button class="view-more-btn" onclick="window.loadMoreExercises(${difficultyLevel})">
                        Load More (${Math.min(remaining, LOAD_MORE_COUNT)} of ${remaining} remaining) ▼
                    </button>
                    <button class="view-less-btn" onclick="window.showLessExercises(${difficultyLevel})" style="margin-left: 10px;">
                        Show Less ▲
                    </button>
                `;
            } else {
                container.innerHTML = `
                    <button class="view-less-btn" onclick="window.showLessExercises(${difficultyLevel})">
                        Show Less ▲
                    </button>
                `;
            }
        }
    }
    
    function showLessExercises(difficultyLevel) {
        const levelExercises = window.groupedExercises[difficultyLevel];
        const INITIAL_COUNT = 4;
        
        if (window.visibleCount[difficultyLevel] <= INITIAL_COUNT) return;
        
        // Get the section element and its position BEFORE making changes
        const sectionElement = document.getElementById(`difficulty-section-${difficultyLevel}`);
        if (!sectionElement) return;
        
        // Get the current position of the section header
        const headerElement = sectionElement.querySelector('.difficulty-header');
        const headerPosition = headerElement ? headerElement.getBoundingClientRect().top + window.scrollY : sectionElement.offsetTop;
        
        // Reset to initial count
        window.visibleCount[difficultyLevel] = INITIAL_COUNT;
        
        // Re-render the grid with only initial exercises
        const grid = document.getElementById(`difficulty-grid-${difficultyLevel}`);
        if (grid) {
            const initialExercises = levelExercises.slice(0, INITIAL_COUNT);
            grid.innerHTML = initialExercises.map(exercise => renderExerciseCard(exercise)).join('');
            highlightSelectedExercises();
        }
        
        // Update the button
        const hasMore = levelExercises.length > INITIAL_COUNT;
        const container = document.getElementById(`view-more-container-${difficultyLevel}`);
        
        if (container) {
            if (hasMore) {
                const remaining = levelExercises.length - INITIAL_COUNT;
                container.innerHTML = `
                    <button class="view-more-btn" onclick="window.loadMoreExercises(${difficultyLevel})">
                        Load More (${Math.min(remaining, LOAD_MORE_COUNT)} of ${remaining} remaining) ▼
                    </button>
                `;
            } else {
                container.innerHTML = '';
            }
        }
        
        // Scroll back to the section header position smoothly
        setTimeout(() => {
            if (headerElement) {
                // Scroll to the header position we saved
                window.scrollTo({
                    top: headerPosition - 140, // 20px padding for better visibility
                    behavior: 'smooth'
                });
            } else if (sectionElement) {
                sectionElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }
        }, 1000);
    }
    
    function getDifficultyColor(level) {
        const colors = {1: '#4CAF50', 2: '#8BC34A', 3: '#FFC107', 4: '#FF9800', 5: '#F44336'};
        return colors[level] || '#757575';
    }
    
    function getDifficultyIcon(level) {
        const icons = {1: '🌱', 2: '👍', 3: '⭐', 4: '🔥', 5: '🏆'};
        return icons[level] || '📋';
    }
    
    function toggleExerciseSelection(exerciseId) {
        const exercise = window.currentExercises.find(e => e.id === exerciseId);
        if (!exercise) return;
        
        const index = window.selectedExercises.findIndex(e => e.id === exerciseId);
        
        if (index === -1) {
            window.selectedExercises.push(exercise);
        } else {
            window.selectedExercises.splice(index, 1);
        }
        
        highlightSelectedExercises();
        updateSelectionSummary();
    }
    
    function highlightSelectedExercises() {
        document.querySelectorAll('.exercise-card').forEach(card => {
            const exerciseId = parseInt(card.dataset.exerciseId);
            if (window.selectedExercises.some(e => e.id === exerciseId)) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });
    }
    
    function updateSelectionSummary() {
        const summaryDiv = document.getElementById('selectionSummary');
        const selectedCountSpan = document.getElementById('selectedExercisesCount');
        const selectedListDiv = document.getElementById('selectedExercisesList');
        const selectedCountDisplay = document.getElementById('selectedCount');
        const prescribeBtn = document.getElementById('prescribeBtn');
        
        if (window.selectedExercises.length > 0) {
            if (summaryDiv) summaryDiv.classList.add('show');
            if (prescribeBtn) prescribeBtn.disabled = false;
            if (selectedCountSpan) selectedCountSpan.textContent = window.selectedExercises.length;
            if (selectedCountDisplay) selectedCountDisplay.textContent = `Selected: ${window.selectedExercises.length}`;
            
            if (selectedListDiv) {
                selectedListDiv.innerHTML = window.selectedExercises.map(exercise => `
                    <div class="selected-badge">
                        ${escapeHtml(exercise.exercise_name)}
                        <span class="remove-exercise" onclick="event.stopPropagation(); window.toggleExerciseSelection(${exercise.id})">✕</span>
                    </div>
                `).join('');
            }
        } else {
            if (summaryDiv) summaryDiv.classList.remove('show');
            if (prescribeBtn) prescribeBtn.disabled = true;
            if (selectedCountDisplay) selectedCountDisplay.textContent = '';
        }
    }
    
    function clearAllSelections() {
        window.selectedExercises = [];
        highlightSelectedExercises();
        updateSelectionSummary();
    }
    
    

    async function submitPrescription() {
        const prescriptionData = {
            patient_id: window.patientId,
            exercises: window.selectedExercises.map(exercise => ({
                exercise_id: exercise.id,
                exercise_name: exercise.exercise_name,
                difficulty_level: exercise.difficulty_level,
            })),
        };
        
        try {
            const response = await fetch('/exercise-app/api/submit-prescription/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(prescriptionData)
            });
            
            
            const data = await response.json();
            
            if (data.success) {
                alert(`Successfully prescribed ${window.selectedExercises.length} exercises!`);
                window.location.href = `/detail-app/patient-exericse-status/${window.patientId}/`;
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error submitting prescription:', error);
            alert('Failed to submit prescription. Please try again.');
        }
    }
    
    function updateStats(count) {
        const exerciseCount = document.getElementById('exerciseCount');
        if (exerciseCount) exerciseCount.textContent = count;
        if (stats) stats.classList.add('show');
    }
    
    function showEmptyState(title, message) {
        if (!exercisesContainer) return;
        exercisesContainer.innerHTML = `
            <div class="empty-state">
                <h3>${escapeHtml(title)}</h3>
                <p>${escapeHtml(message)}</p>
            </div>
        `;
    }
    
    function showErrorState(message) {
        if (!exercisesContainer) return;
        exercisesContainer.innerHTML = `
            <div class="error-state">
                <h3>⚠️ Error Loading Exercises</h3>
                <p>${escapeHtml(message)}</p>
                <p style="margin-top: 10px; font-size: 0.9rem;">Please try again or contact support.</p>
            </div>
        `;
    }
    
    // Make functions available globally
    window.toggleExerciseSelection = toggleExerciseSelection;
    window.loadMoreExercises = loadMoreExercises;
    window.showLessExercises = showLessExercises;
    window.clearAllSelections = clearAllSelections;
    window.submitPrescription = submitPrescription;
    
    console.log('Exercise selectable JS loaded with append-only loading');
});