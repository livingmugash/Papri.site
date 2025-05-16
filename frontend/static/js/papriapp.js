// frontend/static/js/papriapp.js

// Ensure global constants from papriapp.html are accessible
// const CSRF_TOKEN, USER_IS_AUTHENTICATED, USER_EMAIL, USER_FIRST_NAME, USER_LAST_NAME;

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const viewContainer = document.getElementById('view-container');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    const hamburgerMenuButton = document.getElementById('hamburger-menu');
    const dynamicTooltip = document.getElementById('dynamic-tooltip');

    // Search View Elements
    const searchForm = document.getElementById('papri-search-form');
    const searchQueryInput = document.getElementById('search-query-input');
    const searchImageInput = document.getElementById('search-image-input');
    const searchImageFilename = document.getElementById('search-image-filename');
    const searchSourceUrlInput = document.getElementById('search-source-url'); // Optional
    const startSearchButton = document.getElementById('start-search-button');
    const searchStatusDiv = document.getElementById('search-status');
    const searchResultsContainer = document.getElementById('search-results-container');
    const paginationControls = document.getElementById('pagination-controls');
    
    // Filter Elements
    const toggleFiltersButton = document.getElementById('toggle-filters-button');
    const searchFiltersContainer = document.getElementById('search-filters-container');
    const filterPlatformSelect = document.getElementById('filter-platform');
    const filterDurationSelect = document.getElementById('filter-duration');
    const filterDateAfterInput = document.getElementById('filter-date-after');
    const filterSortBySelect = document.getElementById('filter-sort-by');
    const applyFiltersButton = document.getElementById('apply-filters-button');
    const clearFiltersButton = document.getElementById('clear-filters-button');


    // User Profile Elements in Sidebar
    const userAvatarInitial = document.querySelector('#sidebar .user-initial');
    const userNameSidebar = document.querySelector('#sidebar .user-name');
    const userEmailSidebar = document.querySelector('#sidebar .user-email');
    const logoutButton = document.getElementById('logout-button');

    // Settings View Profile Elements
    const userNameSettings = document.querySelector('#settings-view .user-name-settings');
    const userEmailSettings = document.querySelector('#settings-view .user-email-settings');


    let activePlyrInstance = null; // For video previews later
    let tooltipTimeout = null;
    let currentSearchTaskId = null;
    let pollingInterval = null;
    let currentPage = 1;
    let currentFilters = {}; // To store applied filter values
    let currentSortBy = "relevance";
    let currentNextPageUrl = null;
    let currentPreviousPageUrl = null;
    let totalResultsCount = 0;


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
    // const csrftoken = getCookie('csrftoken'); // CSRF_TOKEN is now globally available from HTML script tag

    // --- Initialization ---
    function initializeApp() {
        if (!USER_IS_AUTHENTICATED) {
            // If Django serves this page, @login_required should prevent this.
            // If it's a static SPA and user is not auth'd, redirect to Django's login.
            // Django's allauth will redirect to /app/ after login if LOGIN_REDIRECT_URL is set.
            window.location.href = "/accounts/google/login/?process=login&next=/app/"; // Adjust 'next' as needed
            return;
        }
        initLucideIcons();
        setupNavigation();
        setupUserProfile();
        setupSearchForm();
        setupFilterControls();
        setupLogout();
        // Handle initial hash for view switching
        const initialHash = window.location.hash || '#search';
        switchView(initialHash.substring(1) + '-view', true);
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash || '#search';
            switchView(hash.substring(1) + '-view', true);
        });
        logger("Papri App Initialized");
    }

    function logger(message, type = 'log') {
        console[type](`[PapriApp] ${message}`);
    }

    function initLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        } else {
            logger('Lucide icons library not found.', 'warn');
        }
    }

    function setupNavigation() {
        document.querySelectorAll('#sidebar .nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = item.getAttribute('data-target');
                if (targetId) {
                    switchView(targetId);
                    window.location.hash = item.getAttribute('href'); // Update hash for bookmarking/history
                }
            });
        });

        if (hamburgerMenuButton && sidebar && sidebarBackdrop) {
            hamburgerMenuButton.addEventListener('click', () => toggleSidebar(true));
            sidebarBackdrop.addEventListener('click', () => toggleSidebar(false));
        }
        // Tooltip setup (can use your existing logic from V4)
        document.body.addEventListener('mouseover', handleTooltipShow);
        document.body.addEventListener('mouseout', handleTooltipHide);
    }
    
    function switchView(targetViewId, isInitialOrHistory = false) {
        logger(`Switching to view: ${targetViewId}`);
        if (activePlyrInstance) { activePlyrInstance.destroy(); activePlyrInstance = null; }
        
        viewContainer.querySelectorAll('.app-view').forEach(view => view.classList.add('hidden'));
        const targetView = document.getElementById(targetViewId);
        
        if (targetView) {
            targetView.classList.remove('hidden');
        } else {
            logger(`Target view '${targetViewId}' not found, defaulting to search-view.`, 'warn');
            document.getElementById('search-view')?.classList.remove('hidden');
            if (window.location.hash !== '#search' && !isInitialOrHistory) window.location.hash = '#search';
        }
        
        document.querySelectorAll('#sidebar .nav-item').forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-target') === targetViewId);
        });

        if (!isInitialOrHistory && window.innerWidth < 768) { // Tailwind 'md' breakpoint
             toggleSidebar(false);
        }
    }

    function toggleSidebar(show) {
        if (sidebar && sidebarBackdrop) {
           if (show) {
                sidebar.classList.remove('-translate-x-full'); sidebar.classList.add('translate-x-0');
                sidebarBackdrop.classList.remove('hidden');
            } else {
                sidebar.classList.remove('translate-x-0'); sidebar.classList.add('-translate-x-full');
                sidebarBackdrop.classList.add('hidden');
            }
        }
    }
    
    function setupUserProfile() {
        if (USER_IS_AUTHENTICATED) {
            const displayName = (USER_FIRST_NAME || USER_LAST_NAME) ? `${USER_FIRST_NAME || ''} ${USER_LAST_NAME || ''}`.trim() : USER_EMAIL.split('@')[0];
            const initial = displayName.charAt(0).toUpperCase();

            if (userAvatarInitial) userAvatarInitial.textContent = initial;
            if (userNameSidebar) userNameSidebar.textContent = displayName;
            if (userEmailSidebar) userEmailSidebar.textContent = USER_EMAIL;
            if (userNameSettings) userNameSettings.textContent = displayName;
            if (userEmailSettings) userEmailSettings.textContent = USER_EMAIL;
        } else {
            logger("User not authenticated - profile placeholders not updated.", "warn");
        }
    }

    function setupLogout() {
        if (logoutButton) {
            logoutButton.addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to log out?')) {
                    // Django allauth typically uses a POST to /accounts/logout/ or GET if configured
                    // Create a form and submit it for POST logout to be CSRF safe
                    const logoutForm = document.createElement('form');
                    logoutForm.method = 'POST';
                    logoutForm.action = '/accounts/logout/'; // Allauth logout URL
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = CSRF_TOKEN; // Global CSRF_TOKEN from HTML
                    logoutForm.appendChild(csrfInput);
                    document.body.appendChild(logoutForm);
                    logoutForm.submit();
                }
            });
        }
    }

    function setupSearchForm() {
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                currentPage = 1; // Reset to first page for new search
                initiateSearch();
            });
        }
        if (searchImageInput && searchImageFilename) {
            searchImageInput.addEventListener('change', () => {
                searchImageFilename.textContent = searchImageInput.files.length > 0 ? searchImageInput.files[0].name : '';
            });
        }
        if (searchResultsContainer) {
            searchResultsContainer.addEventListener('click', handleResultCardAction);
        }
    }
    
    function setupFilterControls() {
        if (toggleFiltersButton && searchFiltersContainer) {
            toggleFiltersButton.addEventListener('click', () => {
                searchFiltersContainer.classList.toggle('hidden');
                toggleFiltersButton.innerHTML = searchFiltersContainer.classList.contains('hidden') ? 
                    '<i data-lucide="filter" class="inline-block w-4 h-4 mr-1"></i> Show Filters' : 
                    '<i data-lucide="x" class="inline-block w-4 h-4 mr-1"></i> Hide Filters';
                lucide.createIcons();
            });
        }
        if (applyFiltersButton) {
            applyFiltersButton.addEventListener('click', () => {
                currentPage = 1; // Reset to first page when applying new filters
                collectAndApplyFilters();
                initiateSearch(true); // Pass true to indicate it's a filter-driven search
            });
        }
        if (clearFiltersButton) {
            clearFiltersButton.addEventListener('click', () => {
                // Reset filter UI elements
                if(filterPlatformSelect) filterPlatformSelect.value = "";
                if(filterDurationSelect) filterDurationSelect.value = "";
                if(filterDateAfterInput) filterDateAfterInput.value = "";
                // if(filterDateBeforeInput) filterDateBeforeInput.value = ""; // If you add date before
                if(filterSortBySelect) filterSortBySelect.value = "relevance";
                
                currentPage = 1;
                collectAndApplyFilters(); // This will clear currentFilters object
                initiateSearch(true);
            });
        }
    }

    function collectAndApplyFilters() {
        currentFilters = {};
        if (filterPlatformSelect && filterPlatformSelect.value) currentFilters.platform = filterPlatformSelect.value;
        
        if (filterDurationSelect && filterDurationSelect.value) {
            const duration = filterDurationSelect.value;
            if (duration === "short") currentFilters.duration_max = 300; // < 5 min
            else if (duration === "medium") {currentFilters.duration_min = 300; currentFilters.duration_max = 1200;} // 5-20 min
            else if (duration === "long") currentFilters.duration_min = 1200; // > 20 min
        }
        if (filterDateAfterInput && filterDateAfterInput.value) currentFilters.date_after = filterDateAfterInput.value;
        // if (filterDateBeforeInput && filterDateBeforeInput.value) currentFilters.date_before = filterDateBeforeInput.value;
        
        currentSortBy = (filterSortBySelect && filterSortBySelect.value) ? filterSortBySelect.value : "relevance";
        logger("Filters collected: " + JSON.stringify(currentFilters) + ", Sort: " + currentSortBy);
    }


    async function initiateSearch(isFilterOrSortChange = false) {
        if (!isFilterOrSortChange) { // If it's a brand new search from the main form
            clearPolling();
            searchResultsContainer.innerHTML = '<p class="text-center text-slate-500 italic py-8">Preparing your search...</p>';
            if (activePlyrInstance) { activePlyrInstance.destroy(); activePlyrInstance = null; }
            collectAndApplyFilters(); // Ensure filters are current before new search
        } else {
             logger("Re-initiating search due to filter/sort/page change.");
             // Don't clear task ID if it's just a filter change on existing results,
             // but backend API needs to support re-filtering/sorting an existing task's results or re-querying.
             // For V1, let's assume filters always trigger a new search task or a new query to SearchResultsView.
             // If SearchResultsView handles filters on an existing task ID, this can be simpler.
             // Our current SearchResultsView applies filters to the Video objects from the task's stored IDs.
             // So, if task ID exists and it's just filter/sort, we call fetchAndDisplayResults directly.
             if(currentSearchTaskId && searchStatusDiv.dataset.taskStatus === 'completed') {
                 fetchAndDisplayResults(currentSearchTaskId, currentPage, currentFilters, currentSortBy);
                 return;
             }
             // If no completed task ID, or not a filter change, proceed with new search task.
        }


        const queryText = searchQueryInput.value.trim();
        const imageFile = searchImageInput.files[0];
        const sourceUrl = searchSourceUrlInput.value.trim();

        if (!queryText && !imageFile && !isFilterOrSortChange) { // Only error if truly no input for a new search
            showStatusMessage('Please enter a text query or upload an image.', 'error', searchStatusDiv);
            return;
        }

        const formData = new FormData();
        if (queryText) formData.append('query_text', queryText);
        if (imageFile) formData.append('query_image', imageFile);
        if (sourceUrl) formData.append('video_url', sourceUrl);
        
        // Pass filters that are applied AT INITIATION TIME (if any in your design)
        // formData.append('filters', JSON.stringify(currentFilters)); // Example

        showStatusMessage('<span><span class="spinner mr-2"></span>Initiating AI search...</span>', 'loading', searchStatusDiv);
        startSearchButton.disabled = true;

        try {
            const response = await fetch('/api/search/initiate/', {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF_TOKEN },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Server error during search initiation.' }));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            currentSearchTaskId = data.id;
            searchStatusDiv.dataset.taskStatus = data.status;
            showStatusMessage(`<span><span class="spinner mr-2"></span>Search started (ID: ${currentSearchTaskId.substring(0,8)}...). Awaiting results...</span>`, 'loading', searchStatusDiv);
            startPollingStatus(currentSearchTaskId);

        } catch (error) {
            logger(`Search initiation error: ${error.message}`, 'error');
            showStatusMessage(`Search initiation failed: ${error.message}`, 'error', searchStatusDiv);
            currentSearchTaskId = null;
            startSearchButton.disabled = false;
        }
    }

    function startPollingStatus(taskId) {
        clearPolling();
        logger(`Polling status for task ID: ${taskId}`);
        pollingInterval = setInterval(async () => {
            if (!currentSearchTaskId || currentSearchTaskId !== taskId) { // Stop if task ID changed or cleared
                clearPolling();
                return;
            }
            try {
                const response = await fetch(`/api/search/status/${taskId}/`);
                if (!response.ok) {
                    if (response.status === 404) {
                        showStatusMessage(`Search task ${taskId.substring(0,8)} not found. It might have expired or been an error.`, 'error', searchStatusDiv);
                        clearPolling(); currentSearchTaskId = null; startSearchButton.disabled = false; return;
                    }
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                searchStatusDiv.dataset.taskStatus = data.status;

                if (data.status === 'completed' || data.status === 'partial_results') {
                    clearPolling();
                    showStatusMessage(`Search task ${taskId.substring(0,8)} complete! Fetching results...`, 'success', searchStatusDiv);
                    fetchAndDisplayResults(taskId, currentPage, currentFilters, currentSortBy); // Pass current page, filters, sort
                    startSearchButton.disabled = false;
                } else if (data.status === 'failed') {
                    clearPolling();
                    showStatusMessage(`Search failed for task ${taskId.substring(0,8)}: ${data.error_message || 'Unknown processing error.'}`, 'error', searchStatusDiv);
                    currentSearchTaskId = null; startSearchButton.disabled = false;
                } else { // Still processing or pending
                    showStatusMessage(`<span><span class="spinner mr-2"></span>Search in progress (Status: ${data.status})...</span>`, 'loading', searchStatusDiv);
                }
            } catch (error) {
                logger(`Polling error: ${error.message}`, 'error');
                // Don't clear polling on transient network errors, but maybe after N retries
            }
        }, 3500); // Poll every 3.5 seconds
    }

    function clearPolling() {
        if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; logger("Polling cleared.");}
    }

    async function fetchAndDisplayResults(taskId, page = 1, filters = {}, sortBy = "relevance") {
        logger(`Workspaceing results for task ${taskId}, Page: ${page}, Filters: ${JSON.stringify(filters)}, Sort: ${sortBy}`);
        showStatusMessage('<span><span class="spinner mr-2"></span>Loading results...</span>', 'loading', searchStatusDiv);
        startSearchButton.disabled = true; // Disable while fetching results too

        let queryParams = `?page=${page}&sort_by=${sortBy}`;
        if (filters.platform) queryParams += `&platform=${encodeURIComponent(filters.platform)}`;
        if (filters.duration_min) queryParams += `&duration_min=${filters.duration_min}`;
        if (filters.duration_max) queryParams += `&duration_max=${filters.duration_max}`;
        if (filters.date_after) queryParams += `&date_after=${filters.date_after}`;
        // if (filters.date_before) queryParams += `&date_before=${filters.date_before}`;


        try {
            const response = await fetch(`/api/search/results/${taskId}/${queryParams}`);
            if (!response.ok) throw new Error(`HTTP ${response.status} fetching results`);
            
            const data = await response.json(); // Expects paginated response
            
            searchResultsContainer.innerHTML = ''; // Clear for new results/page
            if (data.results_data && data.results_data.length > 0) {
                displayResultCards(data.results_data);
                setupPagination(data.count, data.next, data.previous, page);
                searchStatusDiv.classList.add('hidden');
            } else {
                searchResultsContainer.innerHTML = '<p class="text-center text-slate-500 italic py-8">No relevant results found for your query or filter combination.</p>';
                paginationControls.innerHTML = ''; paginationControls.classList.add('hidden');
                showStatusMessage('No results found.', 'info', searchStatusDiv);
            }
        } catch (error) {
            logger(`Workspace results error: ${error.message}`, 'error');
            showStatusMessage(`Failed to fetch results: ${error.message}`, 'error', searchStatusDiv);
            searchResultsContainer.innerHTML = '<p class="text-center text-red-500 italic py-8">Error loading results. Please try again.</p>';
        } finally {
            startSearchButton.disabled = false;
        }
    }

    function displayResultCards(results) { // Renamed from displayResults
        results.forEach(video_result => {
            const card = createResultCardElement(video_result); // Changed from _Django, make this the main one
            searchResultsContainer.appendChild(card);
        });
        lucide.createIcons();
    }

    function createResultCardElement(video_result) { // Main card creation function
        const card = document.createElement('div');
        card.id = `result-papri-${video_result.id}`; 
        card.className = 'result-card bg-white p-3 sm:p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 border border-slate-200 flex flex-col md:flex-row gap-4 overflow-hidden';

        const title = video_result.title || 'Untitled Video';
        const thumbnailUrl = video_result.primary_thumbnail_url || `https://via.placeholder.com/320x180.png?text=No+Thumb`;
        let description = video_result.description || 'No description available.';
        if (description.length > 200) description = description.substring(0, 197) + '...';
        
        const pubDateObj = video_result.publication_date ? new Date(video_result.publication_date) : null;
        const publicationDate = pubDateObj ? pubDateObj.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'N/A';
        
        const primarySource = video_result.sources && video_result.sources.length > 0 ? video_result.sources[0] : {};
        const sourcePlatform = primarySource.platform_name || 'Unknown';
        const originalUrl = primarySource.original_url || '#';
        
        // V1 Data from backend
        const textSnippet = video_result.text_snippet;
        const matchTypes = video_result.match_types || [];
        const bestMatchTimestampMs = video_result.best_match_timestamp_ms;

        let matchInfoHtml = '';
        if (matchTypes.length > 0) {
            let typesString = matchTypes.map(type => { // Prettier names
                if (type === 'text_kw') return 'Keywords'; if (type === 'text_sem') return 'Text Meaning';
                if (type === 'vis_cnn') return 'Image Content'; if (type === 'vis_phash') return 'Similar Image';
                if (type === 'fallback_date') return 'Recent'; return type;
            }).join(', ');
            matchInfoHtml += `<p class="text-xs text-indigo-600 font-semibold mt-1.5">Matched via: ${typesString}</p>`;
        }
        if (textSnippet) {
            const cleanSnippet = textSnippet.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            matchInfoHtml += `<p class="text-xs text-slate-600 mt-1 italic bg-slate-50 p-2 rounded">"...${cleanSnippet}..."</p>`;
        }
        if (bestMatchTimestampMs !== null && bestMatchTimestampMs !== undefined) {
            matchInfoHtml += `<p class="text-xs text-green-600 font-semibold mt-1">Key visual match around: ${formatDuration(bestMatchTimestampMs / 1000)}</p>`;
            card.dataset.bestMatchTimestamp = bestMatchTimestampMs / 1000;
        }
        card.dataset.videoUrl = primarySource.embed_url || originalUrl; // For Plyr
        card.dataset.videoSourceType = sourcePlatform.toLowerCase().includes('youtube") ? 'youtube' : (sourcePlatform.toLowerCase().includes('vimeo") ? 'vimeo' : 'html5');
        card.dataset.videoId = primarySource.platform_video_id;


        card.innerHTML = `
            <div class="w-full md:w-48 lg:w-56 flex-shrink-0">
                <div class="aspect-video bg-slate-300 rounded-md overflow-hidden relative group thumbnail-container cursor-pointer" 
                     aria-label="Preview video: ${title} on ${sourcePlatform}"
                     data-plyr-provider="${card.dataset.videoSourceType}" 
                     data-plyr-embed-id="${card.dataset.videoSourceType === 'html5' ? card.dataset.videoUrl : card.dataset.videoId}"> 
                    <img src="${thumbnailUrl}" alt="Thumbnail for ${title}" class="w-full h-full object-cover" loading="lazy">
                    <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity duration-200">
                        <i data-lucide="play" class="w-12 h-12 text-white opacity-0 group-hover:opacity-80 transition-opacity pointer-events-none"></i>
                    </div>
                </div>
                <p class="text-xs text-center text-slate-500 mt-1.5">Source: ${sourcePlatform}</p>
            </div>

            <div class="flex-grow min-w-0">
                <h3 class="text-md sm:text-lg font-semibold text-indigo-700 mb-1 line-clamp-2 hover:text-indigo-800">
                    <a href="${originalUrl}" target="_blank" rel="noopener noreferrer">${title}</a>
                </h3>
                <div class="text-xs text-slate-500 mb-2 flex flex-wrap gap-x-3">
                    <span>Published: ${publicationDate}</span>
                    <span>Duration: ${formatDuration(video_result.duration_seconds)}</span>
                </div>
                <p class="text-sm text-slate-700 line-clamp-3 mb-2">${description}</p>
                
                ${matchInfoHtml}
                
                <div class="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2 items-center">
                    <button class="action-button btn-preview-segment" aria-label="Preview best segment" 
                        ${bestMatchTimestampMs === null ? 'disabled' : ''} title="${bestMatchTimestampMs === null ? 'No specific segment identified' : 'Preview best segment'}"> 
                        <i data-lucide="film" class="action-icon"></i> Preview Segment
                    </button>
                    <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" class="action-button btn-source">
                        <i data-lucide="external-link" class="action-icon"></i> Source
                    </a>
                    <button class="action-button btn-add-collection" aria-label="Add to collection" title="Add to Collection (coming soon)" disabled>
                        <i data-lucide="plus-square" class="action-icon"></i> Collect
                    </button>
                </div>
            </div>
            <div class="video-player-wrapper w-full md:col-span-2 mt-3 hidden rounded-md overflow-hidden">
                <video class="papri-video-player" playsinline controls preload="none"></video>
            </div>
        `;
        return card;
    }

    function handleResultCardAction(event) {
        const button = event.target.closest('button.action-button, .thumbnail-container');
        if (!button) return;

        const card = button.closest('.result-card');
        if (!card) return;
        
        // Close mobile sidebar if an action is taken
        if (window.innerWidth < 768) toggleSidebar(false);

        const videoUrl = card.dataset.videoUrl;
        const videoProvider = card.dataset.videoSourceType;
        const videoPlatformId = card.dataset.videoId; // YouTube/Vimeo ID

        if (button.classList.contains('thumbnail-container') || button.classList.contains('btn-preview-segment')) {
            event.preventDefault();
            const playerWrapper = card.querySelector('.video-player-wrapper');
            const videoElement = card.querySelector('video.papri-video-player');
            
            if (!playerWrapper || !videoElement) {
                logger("Player elements not found in card.", "error");
                return;
            }

            // If this player is already active, destroy it (toggle off)
            if (activePlyrInstance && activePlyrInstance.elements.container.closest('.result-card') === card) {
                activePlyrInstance.destroy();
                activePlyrInstance = null;
                playerWrapper.classList.add('hidden');
                return;
            }
            
            // Destroy any other active player
            if (activePlyrInstance) {
                const oldCard = activePlyrInstance.elements.container.closest('.result-card');
                if (oldCard) {
                     oldCard.querySelector('.video-player-wrapper')?.classList.add('hidden');
                }
                activePlyrInstance.destroy();
                activePlyrInstance = null;
            }

            // Setup new player
            playerWrapper.classList.remove('hidden');
            videoElement.dataset.plyrProvider = videoProvider;
            if (videoProvider === 'html5') {
                videoElement.src = videoUrl; // For direct MP4 links
            } else {
                videoElement.dataset.plyrEmbedId = videoPlatformId;
            }
            
            activePlyrInstance = new Plyr(videoElement, {
                autoplay: true,
                // controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'],
            });

            activePlyrInstance.on('ready', () => {
                if (button.classList.contains('btn-preview-segment') && card.dataset.bestMatchTimestamp) {
                    const startTime = parseFloat(card.dataset.bestMatchTimestamp);
                    if (!isNaN(startTime) && startTime > 0) {
                        activePlyrInstance.currentTime = startTime;
                        logger(`Player ready, seeking to timestamp: ${startTime}`);
                    }
                }
                activePlyrInstance.play();
            });
            activePlyrInstance.on('ended', () => { // Optionally hide player on end
                playerWrapper.classList.add('hidden');
                activePlyrInstance.destroy();
                activePlyrInstance = null;
            });
             // Scroll the card into view if needed, especially the player
             playerWrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        } else if (button.classList.contains('btn-source')) {
            // Default anchor behavior handles this
        } else if (button.classList.contains('btn-add-collection')) {
            alert('Add to collection feature coming soon!');
        }
    }

    function setupPagination(count, nextUrl, prevUrl, currentPageNum) {
        paginationControls.innerHTML = ''; // Clear old controls
        totalResultsCount = count;

        if (count <= (StandardResultsSetPagination.page_size || 12) && !nextUrl && !prevUrl) { // Assuming StandardResultsSetPagination is accessible or use hardcoded page_size
            paginationControls.classList.add('hidden');
            return;
        }
        paginationControls.classList.remove('hidden');

        const prevButton = document.createElement('button');
        prevButton.innerHTML = `<i data-lucide="arrow-left" class="mr-1 h-4 w-4 inline"></i> Previous`;
        prevButton.className = "px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50";
        prevButton.disabled = !prevUrl;
        if (prevUrl) {
            prevButton.addEventListener('click', () => {
                currentPage--; // Update global current page
                fetchAndDisplayResults(currentSearchTaskId, currentPage, currentFilters, currentSortBy);
            });
        }
        paginationControls.appendChild(prevButton);

        const pageInfo = document.createElement('span');
        const itemsPerPage = (StandardResultsSetPagination.page_size || 12);
        const totalPages = Math.ceil(count / itemsPerPage);
        pageInfo.textContent = `Page ${currentPageNum} of ${totalPages} (Total: ${count})`;
        pageInfo.className = "text-sm text-slate-700 px-3";
        paginationControls.appendChild(pageInfo);

        const nextButton = document.createElement('button');
        nextButton.innerHTML = `Next <i data-lucide="arrow-right" class="ml-1 h-4 w-4 inline"></i>`;
        nextButton.className = "px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50";
        nextButton.disabled = !nextUrl;
        if (nextUrl) {
            nextButton.addEventListener('click', () => {
                currentPage++; // Update global current page
                fetchAndDisplayResults(currentSearchTaskId, currentPage, currentFilters, currentSortBy);
            });
        }
        paginationControls.appendChild(nextButton);
        lucide.createIcons();
    }

    // --- Utility Functions ---
    function formatDuration(totalSeconds) {
        if (totalSeconds === null || totalSeconds === undefined || totalSeconds <= 0) return 'N/A';
        const h = Math.floor(totalSeconds / 3600); const m = Math.floor((totalSeconds % 3600) / 60); const s = Math.floor(totalSeconds % 60);
        return (h > 0 ? `${h}:${String(m).padStart(2, '0')}:` : `${String(m).padStart(2, '0')}:`) + String(s).padStart(2, '0');
    }
    function showStatusMessage(message, type = 'info', element) { // ... (as before)
        if (!element) return; element.innerHTML = message; element.className = 'search-status-message mb-4 p-3 rounded-md text-sm ';
        const typeClasses = {'error': 'bg-red-100 text-red-700','success': 'bg-green-100 text-green-700','loading': 'bg-blue-100 text-blue-700','info': 'bg-yellow-100 text-yellow-700'};
        element.classList.add(...(typeClasses[type] || typeClasses.info).split(' ')); element.classList.remove('hidden');
    }
    function handleTooltipShow(e) { /* ... (Your existing V4 logic, ensure dynamicTooltip is defined) ... */ }
    function handleTooltipHide() { /* ... (Your existing V4 logic) ... */ }


    // --- Start the app ---
    initializeApp();
});
