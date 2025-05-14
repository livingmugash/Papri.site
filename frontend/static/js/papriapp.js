// frontend/static/js/papriapp.js

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const viewContainer = document.getElementById('view-container');
    const searchForm = document.getElementById('papri-search-form'); // **NEW: Assume your search form has this ID**
    const searchQueryInput = document.getElementById('search-query-input');
    const searchImageInput = document.getElementById('search-image-input'); // **NEW: Assume your image input has this ID**
    const searchSourceUrlInput = document.getElementById('search-source-url'); // From your HTML
    
    const searchStatusDiv = document.getElementById('search-status');
    const searchResultsContainer = document.getElementById('search-results-container');
    
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    const hamburgerMenuButton = document.getElementById('hamburger-menu');
    const dynamicTooltip = document.getElementById('dynamic-tooltip');

    let activePlyrInstance = null;
    let tooltipTimeout = null;
    let currentSearchTaskId = null;
    let pollingInterval = null;

    // --- CSRF Token Helper ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // --- Initial Setup ---
    initLucideIcons();
    setupNavigationAndTooltips();
    setupSearchForm(); // **MODIFIED**
    setupReferralCopy(); // Keep if functionality is present
    setupSettingsActions(); // Keep if functionality is present
    setupLogout(); // Keep or adapt for Django logout
    updateUserInfoPlaceholders(); // Adapt to fetch user info if needed

    // --- Initialization Functions ---
    function initLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        } else {
            console.warn('Lucide icons library not found.');
        }
    }

    function setupNavigationAndTooltips() {
        // ... (Your existing navigation and tooltip logic from papriapp.js) ...
        // Ensure switchView correctly handles showing/hiding views.
        const initialHash = window.location.hash || '#search';
        const initialTargetId = initialHash.substring(1) + '-view';
        switchView(initialTargetId, true);

        document.querySelectorAll('#sidebar .nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = item.getAttribute('data-target');
                if (targetId) {
                    switchView(targetId);
                    window.location.hash = item.getAttribute('href');
                }
            });
        });

        window.addEventListener('hashchange', () => {
            const hash = window.location.hash || '#search';
            const targetId = hash.substring(1) + '-view';
            switchView(targetId, true);
        });

        if (hamburgerMenuButton && sidebar && sidebarBackdrop) {
            hamburgerMenuButton.addEventListener('click', () => toggleSidebar(true));
            sidebarBackdrop.addEventListener('click', () => toggleSidebar(false));
        }
        // Global Tooltip Logic (using aria-label)
        document.body.addEventListener('mouseover', handleTooltipShow);
        document.body.addEventListener('mouseout', handleTooltipHide);
        document.body.addEventListener('focusin', handleTooltipShow);
        document.body.addEventListener('focusout', handleTooltipHide);
    }
    
    function toggleSidebar(show) {
        // ... (Your existing toggleSidebar logic) ...
    }
    function handleTooltipShow(e) { /* ... */ }
    function handleTooltipHide(e) { /* ... */ }
    function positionTooltip(targetElement) { /* ... */ }


    function setupSearchForm() {
        if (searchForm) {
            searchForm.addEventListener('submit', handleSearchSubmit);
        } else {
            console.warn("Search form with ID 'papri-search-form' not found.");
        }
        // Event listener for result actions (play, source, etc.)
        if (searchResultsContainer) {
            searchResultsContainer.addEventListener('click', handleResultAction);
            // searchResultsContainer.addEventListener('keypress', handleResultKeyPress); // If needed
        }
    }

    // --- Search Handling (NEW/MODIFIED) ---
    async function handleSearchSubmit(event) {
        event.preventDefault();
        clearPolling(); // Clear any previous polling
        searchResultsContainer.innerHTML = ''; // Clear previous results
        if (activePlyrInstance) { activePlyrInstance.destroy(); activePlyrInstance = null; }

        const queryText = searchQueryInput.value.trim();
        const imageFile = searchImageInput.files[0];
        // const sourceUrl = searchSourceUrlInput.value.trim(); // Add if you have this input

        if (!queryText && !imageFile) {
            showStatusMessage('Please enter a search query or upload an image.', 'error', searchStatusDiv);
            return;
        }

        const formData = new FormData();
        if (queryText) {
            formData.append('query_text', queryText);
        }
        if (imageFile) {
            formData.append('query_image', imageFile);
        }
        // if (sourceUrl) {
        //     formData.append('video_url', sourceUrl); // If your backend API accepts this
        // }
        // Add any filters from UI to formData if needed

        showStatusMessage('<span><span class="spinner mr-2"></span>Initiating AI search...</span>', 'loading', searchStatusDiv);

        try {
            const response = await fetch('/api/search/initiate/', { // Your Django API endpoint
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    // 'Content-Type': 'multipart/form-data' is set automatically by browser for FormData
                },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Failed to initiate search. Server error.' }));
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            currentSearchTaskId = data.id; // Assuming 'id' is the task_id field from SearchTaskSerializer
            showStatusMessage(`<span><span class="spinner mr-2"></span>Search started (ID: ${currentSearchTaskId.substring(0,8)}...). Checking status...</span>`, 'loading', searchStatusDiv);
            startPollingStatus(currentSearchTaskId);

        } catch (error) {
            console.error("Search initiation error:", error);
            showStatusMessage(`Search initiation failed: ${error.message}`, 'error', searchStatusDiv);
            currentSearchTaskId = null;
        }
    }

    function startPollingStatus(taskId) {
        clearPolling(); // Clear existing interval if any

        pollingInterval = setInterval(async () => {
            if (!currentSearchTaskId) { // Safety check
                clearPolling();
                return;
            }
            try {
                const response = await fetch(`/api/search/status/${taskId}/`);
                if (!response.ok) {
                    // If 404, task might not exist or was invalid
                    if (response.status === 404) {
                         showStatusMessage(`Search task ${taskId.substring(0,8)} not found.`, 'error', searchStatusDiv);
                         clearPolling();
                         currentSearchTaskId = null;
                         return;
                    }
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const data = await response.json();

                if (data.status === 'completed' || data.status === 'partial_results') {
                    clearPolling();
                    showStatusMessage(`Search complete! Fetching results for task ${taskId.substring(0,8)}...`, 'success', searchStatusDiv);
                    fetchResults(taskId);
                } else if (data.status === 'failed') {
                    clearPolling();
                    showStatusMessage(`Search failed for task ${taskId.substring(0,8)}: ${data.error_message || 'Unknown error'}`, 'error', searchStatusDiv);
                    currentSearchTaskId = null;
                } else {
                    // Still processing or pending
                    showStatusMessage(`<span><span class="spinner mr-2"></span>Search in progress (Status: ${data.status})...</span>`, 'loading', searchStatusDiv);
                }
            } catch (error) {
                console.error("Polling error:", error);
                showStatusMessage(`Error checking search status: ${error.message}`, 'error', searchStatusDiv);
                // Optionally stop polling on persistent errors or after a timeout
                // clearPolling();
            }
        }, 3000); // Poll every 3 seconds
    }

    function clearPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    async function fetchResults(taskId) {
        try {
            const response = await fetch(`/api/search/results/${taskId}/`);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();

            // Assuming data.results_data is an array of video objects from your backend
            // This will be based on VideoResultSerializer or similar
            if (data.results_data && data.results_data.length > 0) {
                displayResults(data.results_data); // Use your existing displayResults or adapt it
                searchStatusDiv.classList.add('hidden'); // Hide status on successful display
            } else {
                showStatusMessage('No relevant results found for your query.', 'info', searchStatusDiv);
            }
        } catch (error) {
            console.error("Fetch results error:", error);
            showStatusMessage(`Failed to fetch results: ${error.message}`, 'error', searchStatusDiv);
        } finally {
            currentSearchTaskId = null; // Reset for next search
        }
    }

    // --- Result Display and Actions ---
    // Adapt your existing createResultCardElement and displayResults functions
    // The 'result' object passed to createResultCardElement will now come from our Django backend
    // Ensure the fields match what VideoResultSerializer provides.
    function displayResults(results) {
        searchResultsContainer.innerHTML = ''; // Clear previous
        if (results.length === 0) {
            searchResultsContainer.innerHTML = '<p class="text-center text-gray-500 italic">No results found.</p>';
            return;
        }
        results.forEach(result => {
            // Assuming 'result' has: id, title, description, publication_date, primary_thumbnail_url, sources
            // And each source in 'sources' has: platform_name, original_url, embed_url
            // You'll need to adapt createResultCardElement to use these fields.
            const card = createResultCardElement_Django(result); // **MODIFIED to a new function for clarity**
            searchResultsContainer.appendChild(card);
        });
        initLucideIcons(); // Re-initialize icons if new ones are added
    }

    function createResultCardElement_Django(result) {
        const card = document.createElement('div');
        // Unique ID for the card, can use result.id from Video model
        card.id = `result-${result.id}`; 
        card.className = 'result-card bg-white p-3 sm:p-4 rounded-lg shadow border border-gray-200 flex flex-col md:flex-row gap-3 sm:gap-4 overflow-hidden';

        // Extracting data (adjust based on your VideoResultSerializer structure)
        const title = result.title || 'Untitled Video';
        const thumbnailUrl = result.primary_thumbnail_url || 'https://via.placeholder.com/320x180.png?text=No+Thumbnail';
        const description = result.description || 'No description available.';
        const publicationDate = result.publication_date ? new Date(result.publication_date).toLocaleDateString() : 'N/A';
        
        // Assuming 'sources' is an array and we take the first one for display simplicity
        const primarySource = result.sources && result.sources.length > 0 ? result.sources[0] : null;
        const sourcePlatform = primarySource ? primarySource.platform_name : 'Unknown';
        const originalUrl = primarySource ? primarySource.original_url : '#';
        
        // Data attributes for player (these will be filled by AI agent later)
        // card.dataset.startTime = result.matched_start_time || 0;
        // card.dataset.endTime = result.matched_end_time || result.duration_seconds || 0;
        // card.dataset.videoUrl = primarySource ? (primarySource.embed_url || primarySource.original_url) : '#';

        // Simplified card structure for now - Adapt your V3/V4 createResultCardElement structure here
        card.innerHTML = `
            <div class="w-full md:w-48 lg:w-56 flex-shrink-0">
                <div class="aspect-video bg-gray-300 rounded overflow-hidden relative group thumbnail-container" 
                     aria-label="Preview video: ${title}">
                    <img src="${thumbnailUrl}" alt="Video thumbnail for ${title}" class="w-full h-full object-cover" loading="lazy">
                    <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity duration-200">
                        <i data-lucide="play-circle" class="w-10 h-10 text-white opacity-0 group-hover:opacity-75 transition-opacity pointer-events-none"></i>
                    </div>
                </div>
                <p class="text-xs text-center text-gray-500 mt-1 md:mt-1.5">Source: ${sourcePlatform}</p>
            </div>

            <div class="flex-grow min-w-0">
                <h3 class="text-md sm:text-lg font-semibold text-indigo-700 mb-1 line-clamp-2">${title}</h3>
                <p class="text-xs text-gray-500 mb-2">Published: ${publicationDate}</p>
                <p class="text-sm text-gray-600 line-clamp-3 mb-3">${description}</p>
                
                <div class="flex flex-wrap gap-1.5 sm:gap-2 items-center">
                    <button class="action-button btn-preview" aria-label="Preview this video" disabled> 
                        <i data-lucide="play-circle" class="action-icon"></i> Preview
                    </button>
                    <a href="${originalUrl}" target="_blank" class="action-button btn-source" aria-label="Open original source">
                        <i data-lucide="external-link" class="action-icon"></i> Source
                    </a>
                    <button class="action-button btn-save-clip" aria-label="Save this video" disabled>
                        <i data-lucide="bookmark-plus" class="action-icon"></i> Save 
                    </button>
                    </div>
            </div>
        `;
        // Add more details and actions as your AI backend provides them (timestamps, snippets etc.)
        // The btn-preview, btn-save-clip etc. will need data attributes set with video URLs and segment times
        // once the AI provides that level of detail. For now, they might be disabled or link to full source.
        return card;
    }

    // --- Event Handlers for result card actions (play, source, etc.) ---
    // Your existing handleResultAction can be adapted.
    // It needs to get video URLs and segment times from card.dataset attributes.
    // Since the AI agent part is not yet returning these specific details,
    // these actions might be limited initially.
    function handleResultAction(e) {
        const target = e.target;
        const button = target.closest('button, a, .thumbnail-container');
        if (!button) return;

        const card = button.closest('.result-card');
        if (!card) return;
        
        if (window.innerWidth < 768) { // Assuming md breakpoint is 768px
            toggleSidebar(false);
        }

        if (button.tagName === 'BUTTON' || button.classList.contains('thumbnail-container') || button.classList.contains('share-item')) {
             e.preventDefault();
        }

        // const videoUrl = card.dataset.videoUrl; // These will be set once AI provides them
        // const startTime = parseFloat(card.dataset.startTime);
        // const endTime = parseFloat(card.dataset.endTime);

        if (button.classList.contains('btn-preview') || button.classList.contains('thumbnail-container')) {
             // TODO: Implement player logic once videoUrl and segment times are available
             alert('Preview functionality to be implemented with AI results.');
             // activatePlayer(card, videoUrl, startTime, endTime, 'preview');
        } else if (button.classList.contains('btn-source')) {
             // This is already an anchor tag, default behavior will open link.
             // If it was a button: window.open(button.href, '_blank', 'noopener,noreferrer');
        } else if (button.classList.contains('btn-save-clip')) {
             alert('Save clip functionality to be implemented.');
        }
        // ... other actions from your V4 ...
    }
    
    // --- Utility Functions (formatTime, showStatusMessage) ---
    function showStatusMessage(message, type = 'info', element) {
        if (!element) return;
        element.innerHTML = message; // Allow HTML for spinner etc.
        element.className = 'mb-4 p-3 rounded-md text-sm '; // Reset classes
        switch (type) {
            case 'error': element.classList.add('bg-red-100', 'text-red-700'); break;
            case 'success': element.classList.add('bg-green-100', 'text-green-700'); break;
            case 'loading': element.classList.add('bg-blue-100', 'text-blue-700'); break;
            case 'info': default: element.classList.add('bg-yellow-100', 'text-yellow-700'); break;
        }
        element.classList.remove('hidden');
    }

    function switchView(targetId, isInitialOrHistory = false) {
        // ... (Your existing switchView logic) ...
        if (activePlyrInstance) {
            activePlyrInstance.destroy(); activePlyrInstance = null;
        }
        viewContainer.querySelectorAll('.app-view').forEach(view => view.classList.add('hidden'));
        const targetView = document.getElementById(targetId);
        if (targetView) {
            targetView.classList.remove('hidden');
        } else {
            // Fallback to search view if target not found
            document.getElementById('search-view')?.classList.remove('hidden');
            if (window.location.hash !== '#search' && !isInitialOrHistory) window.location.hash = '#search';
        }
        document.querySelectorAll('#sidebar .nav-item').forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-target') === targetId);
        });
        if (!isInitialOrHistory && window.innerWidth < 768) {
             toggleSidebar(false);
        }
    }

    // --- Placeholder/Demo functions (adapt or replace) ---
    function setupReferralCopy() { /* ... (Your existing V4 logic) ... */ }
    function setupSettingsActions() { /* ... (Your existing V4 logic) ... */ }
    function setupLogout() {
        // Adapt for Django logout: typically a link to '/accounts/logout/'
        const logoutButton = document.getElementById('logout-button');
        if (logoutButton) {
            logoutButton.addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to log out?')) {
                    // Make a POST request to Django's logout or redirect
                    // For simple GET-based logout (if allauth is configured for it):
                    window.location.href = '/accounts/logout/';
                }
            });
        }
    }
    function updateUserInfoPlaceholders() {
        // TODO: Fetch user details from an API endpoint like /api/auth/user/
        // and update .user-name, .user-initial, #profile-email etc.
        // For now, keep placeholders or simple demo values.
        fetch('/api/auth/status/') // Use the auth_status endpoint
            .then(response => response.json())
            .then(data => {
                if (data.is_authenticated === false || !data.email) { // Check if actually authenticated
                    // User not logged in, redirect to login page or show login prompt
                    // For now, use demo user if no auth, or redirect:
                    // window.location.href = '/accounts/login/?next=/app/'; // Redirect to login if not on app page.
                    console.log("User not authenticated, using demo placeholders.");
                    const userName = "Demo User";
                    const userInitial = userName.charAt(0).toUpperCase();
                    document.querySelectorAll('.user-name').forEach(el => el.textContent = userName);
                    document.querySelectorAll('.user-initial').forEach(el => el.textContent = userInitial);
                    const emailElement = document.getElementById('profile-email');
                    if (emailElement) emailElement.textContent = "demo@example.com";
                } else {
                    const


function displayResults(results_data) { // results_data is the array from VideoResultSerializer
    searchResultsContainer.innerHTML = ''; 
    if (!results_data || results_data.length === 0) { // Check if results_data itself is undefined or empty
        searchResultsContainer.innerHTML = '<p class="text-center text-gray-500 italic">No results found for your query.</p>';
        return;
    }
    results_data.forEach(video_result => { // Each item is a serialized Video object
        const card = createResultCardElement_Django(video_result);
        searchResultsContainer.appendChild(card);
    });
    initLucideIcons(); 
}

function createResultCardElement_Django(video_result) { // video_result is one item from VideoResultSerializer output
    const card = document.createElement('div');
    card.id = `result-${video_result.id}`; // Papri Video ID
    card.className = 'result-card bg-white p-3 sm:p-4 rounded-lg shadow border border-gray-200 flex flex-col md:flex-row gap-3 sm:gap-4 overflow-hidden';

    const title = video_result.title || 'Untitled Video';
    const thumbnailUrl = video_result.primary_thumbnail_url || `https://via.placeholder.com/320x180.png?text=${encodeURIComponent(title.substring(0,10))}`;
    const description = video_result.description ? (video_result.description.length > 150 ? video_result.description.substring(0, 147) + '...' : video_result.description) : 'No description available.';
    const publicationDate = video_result.publication_date ? new Date(video_result.publication_date).toLocaleDateString() : 'N/A';
    
    // 'sources' is an array of VideoSourceResultSerializer outputs
    const primarySourceInfo = video_result.sources && video_result.sources.length > 0 ? video_result.sources[0] : null;
    const sourcePlatform = primarySourceInfo ? primarySourceInfo.platform_name : 'Unknown Source';
    const originalUrl = primarySourceInfo ? primarySourceInfo.original_url : '#';
    
    // For player functionality later:
    // card.dataset.videoPapriId = video_result.id;
    // if (primarySourceInfo) {
    //     card.dataset.videoSourceUrl = primarySourceInfo.embed_url || primarySourceInfo.original_url;
    // }
    // card.dataset.duration = video_result.duration_seconds || 0;

    card.innerHTML = `
        <div class="w-full md:w-48 lg:w-56 flex-shrink-0">
            <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" class="block aspect-video bg-gray-300 rounded overflow-hidden relative group thumbnail-container" 
                 aria-label="Watch video: ${title} on ${sourcePlatform}">
                <img src="${thumbnailUrl}" alt="Video thumbnail for ${title}" class="w-full h-full object-cover" loading="lazy">
                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity duration-200">
                    <i data-lucide="play-circle" class="w-10 h-10 text-white opacity-0 group-hover:opacity-75 transition-opacity pointer-events-none"></i>
                </div>
            </a>
            <p class="text-xs text-center text-gray-500 mt-1 md:mt-1.5">Source: ${sourcePlatform}</p>
        </div>

        <div class="flex-grow min-w-0">
            <h3 class="text-md sm:text-lg font-semibold text-indigo-700 mb-1 line-clamp-2">
                <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" class="hover:underline">${title}</a>
            </h3>
            <p class="text-xs text-gray-500 mb-2">Published: ${publicationDate} | Duration: ${formatDuration(video_result.duration_seconds)}</p>
            <p class="text-sm text-gray-600 line-clamp-3 mb-3">${description}</p>
            
            <div class="flex flex-wrap gap-1.5 sm:gap-2 items-center">
                <button class="action-button btn-preview" data-video-id="${video_result.id}" aria-label="Preview this video (feature coming)" disabled> 
                    <i data-lucide="play-circle" class="action-icon"></i> Preview
                </button>
                <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" class="action-button btn-source" aria-label="Open original source">
                    <i data-lucide="external-link" class="action-icon"></i> Source
                </a>
                <button class="action-button btn-save-clip" data-video-id="${video_result.id}" aria-label="Save this video (feature coming)" disabled>
                    <i data-lucide="bookmark-plus" class="action-icon"></i> Save 
                </button>
                </div>
        </div>
    `;
    return card;
}

// Helper function to format duration
function formatDuration(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined || totalSeconds <= 0) {
        return 'N/A';
    }
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    const paddedSeconds = String(seconds).padStart(2, '0');
    const paddedMinutes = String(minutes).padStart(2, '0');

    if (hours > 0) {
        return `${hours}:${paddedMinutes}:${paddedSeconds}`;
    }
    return `${paddedMinutes}:${paddedSeconds}`;
}


// ... (showStatusMessage, switchView, setupReferralCopy, setupSettingsActions, setupLogout, updateUserInfoPlaceholders, handleResultAction etc.) ...
// Ensure handleResultAction is adapted for any data attributes you add to buttons for interaction.

// In createResultCardElement_Django(video_result)

    // ...
    const matchTypes = video_result.match_types || [];
    let matchTypesHtml = '';
    if (matchTypes.length > 0) {
        matchTypesHtml = `<p class="text-xs text-blue-500 mt-1">Matched on: ${matchTypes.join(', ').replace(/_/g, ' ')}</p>`;
    }
    // ...
    // Add matchTypesHtml to your card.innerHTML, for example:
    // card.innerHTML = `
    //     ...
    //     <div class="flex-grow min-w-0">
    //         ... (title, pub_date, description) ...
    //         ${matchTypesHtml} 
    //         <div class="flex flex-wrap gap-1.5 sm:gap-2 items-center mt-2"> 
    //             ... (buttons) ...
    //         </div>
    //     </div>
    // `;
    // ...

// frontend/static/js/papriapp.js
// In createResultCardElement_Django(video_result)

    // ...
    const matchTypes = video_result.match_types || [];
    const bestMatchTimestampMs = video_result.best_match_timestamp_ms;
    let matchInfoHtml = '';

    if (matchTypes.length > 0) {
        let typesString = matchTypes.map(type => {
            if (type === 'text_kw') return 'Keywords';
            if (type === 'text_sem') return 'Text Meaning';
            if (type === 'vis_cnn') return 'Image Similarity';
            if (type === 'vis_phash') return 'Exact Image Match';
            return type;
        }).join(', ');
        matchInfoHtml += `<p class="text-xs text-blue-600 font-medium mt-1">Matched on: ${typesString}</p>`;
    }
    if (bestMatchTimestampMs !== null && bestMatchTimestampMs !== undefined) {
        matchInfoHtml += `<p class="text-xs text-green-600 mt-1">Best visual match around: ${formatDuration(bestMatchTimestampMs / 1000)}</p>`;
        // Add data attribute to card or preview button for this timestamp
        card.dataset.bestMatchTimestamp = bestMatchTimestampMs / 1000; // in seconds
    }
    // ...
    // Add matchInfoHtml to your card.innerHTML:
    // card.innerHTML = `
    //     ...
    //     <div class="flex-grow min-w-0">
    //         ... (title, pub_date, description) ...
    //         ${matchInfoHtml} {/* Display match info */}
    //         <div class="flex flex-wrap gap-1.5 sm:gap-2 items-center mt-2"> 
    //             ... (buttons) ...
    //             {/* Modify preview button to use bestMatchTimestamp if available */}
    //         </div>
    //     </div>
    // `;
    // ...
                    
