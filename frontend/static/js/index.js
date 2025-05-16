// frontend/static/js/index.js (Was papri.js in your initial files)

// --- Translations Dictionary ---
// (Using your existing comprehensive translations object)
const translations = {
    'en': { // English (Default)
        'page_title': 'Papri - Instantly Find Any Moment in Your Videos',
        'nav_try': 'Try Papri', 'nav_why': 'Why Papri?', 'nav_how': 'How it Works', 'nav_pricing': 'Pricing', 'nav_faq': 'FAQ',
        'button_login': 'Login', 'button_signup': 'Sign Up',
        'hero_badge': 'New AI-Powered Video Search',
        'hero_title': 'Stop Searching, Start Finding. #ShazamForContent!',
        'hero_subtitle': 'Instantly Access Any Moment<br class="sm:hidden"> in Any Online Video Content.',
        'hero_button_try': 'Try Papri Free', 'hero_button_demo': 'Watch Demo',
        'demo_title': 'See Papri in Action',
        'demo_subtitle': 'Watch this short demo to understand how Papri\'s AI can revolutionize your video search experience.',
        'try_title': 'Experience Papri Now',
        'try_subtitle': 'Enter a link (e.g., YouTube, Vimeo) or upload a file/screenshot, tell us what you\'re looking for, and let our AI pinpoint the exact moment (demo).',
        'try_label_source_url': 'Video URL (e.g., YouTube, Vimeo)',
        'try_label_source_upload': 'Or Upload Screenshot/Image',
        'try_label_query': 'What are you looking for in the video?',
        'try_button_find': 'Find Moment (Demo)',
        'try_trial_counter': 'You have {count} free demo search remaining.',
        'try_trial_counter_plural': 'You have {count} free demo searches remaining.',
        'try_trial_limit': 'You\'ve used all your free demo searches.',
        'try_trial_subscribe': 'Sign Up to search with the full Papri app!',
        'try_file_selected_prefix': 'Selected: ',
        'why_title': 'Tired of Aimlessly Scrubbing Videos?',
        'why_subtitle': 'Papri\'s AI understands your favorite video content, letting you find exactly what you need, instantly.',
        'why_feature1_title': 'Instant Pinpoint Accuracy',
        'why_feature1_desc': 'Describe what you\'re looking for and Papri takes you to the precise moment in seconds.',
        'why_feature2_title': 'Search *Inside* Your Content',
        'why_feature2_desc': 'Our AI analyzes transcripts, visual elements, and context for truly relevant results.',
        'why_feature3_title': 'Save Time & Boost Productivity',
        'why_feature3_desc': 'Reclaim hours. Perfect for creators, researchers, students, and video professionals.',
        'steps_title': 'Get Started in 3 Simple Steps',
        'steps_step1_title': 'Provide Content', 'steps_step1_desc': 'Paste a link or upload your video/image.',
        'steps_step2_title': 'Describe Moment', 'steps_step2_desc': 'Tell Papri what you\'re searching for.',
        'steps_step3_title': 'Find Instantly', 'steps_step3_desc': 'AI presents the exact matching segment.',
        'pricing_title': 'Ready to Unlock Full Power?',
        'pricing_subtitle': 'Go beyond the free trial and revolutionize how you interact with video content.',
        'pricing_plan_badge': 'Pro Plan',
        'pricing_plan_name': 'Papri Pro',
        'pricing_plan_audience': 'For individuals and small teams.',
        'pricing_per_month': '/ month',
        'pricing_billing_info': 'Billed monthly, cancel anytime.',
        'pricing_feature_searches': 'Unlimited AI content searches',
        'pricing_feature_sources_full': 'YouTube, Vimeo, Dailymotion, PeerTube & more',
        'pricing_feature_deep_analysis': 'Deep Transcript & Visual Analysis',
        'pricing_feature_timestamps': 'Timestamped segment results',
        'pricing_feature_segments': 'Download & Trim segments (Coming Soon)',
        'pricing_feature_support': 'Priority email support',
        'pricing_cta_button': 'Get Started with Pro',
        'pricing_enterprise_prompt': 'Need enterprise features?', 'pricing_contact_sales': 'Contact Sales',
        'pricing_rate_disclaimer': '*Exchange rate is approximate. Final charge processed by payment provider.',
        'faq_title': 'Frequently Asked Questions',
        'faq_q1_title': 'How accurate is the AI search?', 'faq_q1_desc': 'Papri uses state-of-the-art AI... (Full description)',
        'faq_q2_title': 'What video formats and sources are supported?', 'faq_q2_desc': 'Currently, Papri supports links from major platforms... (Full description)',
        // Add ALL other FAQ keys and any other translatable strings from index.html
        'footer_text': `© {year} Papri. Find your video moments, faster.`,
        'footer_privacy': 'Privacy Policy', 'footer_terms': 'Terms of Service', 'footer_contact': 'Contact Us',
    },
    'sw': { // Swahili example
        'page_title': 'Papri - Pata Kipande Chochote Kwenye Video Zako Mara Moja',
        'nav_try': 'Jaribu Papri', 'nav_why': 'Kwa Nini Papri?', 'nav_how': 'Inavyofanya Kazi', 'nav_pricing': 'Bei', 'nav_faq': 'Maswali',
        'button_login': 'Ingia', 'button_signup': 'Jisajili',
        'hero_badge': 'Utafutaji Mpya wa Video kwa Akili Bandia',
        'hero_title': 'Acha Kutafuta, Anza Kupata. #ShazamYaMaudhui!',
        'hero_subtitle': 'Fikia Kipande Chochote Mara Moja<br class="sm:hidden"> Katika Maudhui Yoyote Mtandaoni.',
        'hero_button_try': 'Jaribu Papri Bure (Demo)', 'hero_button_demo': 'Tazama Demo',
        'demo_title': 'Ona Papri Ikifanya Kazi',
        'demo_subtitle': 'Tazama demo hii fupi kuelewa jinsi akili bandia ya Papri inavyoweza kubadilisha utafutaji wako wa video.',
        'try_title': 'Tumia Papri Sasa (Demo)',
        'try_subtitle': 'Weka linki (k.m., YouTube) au pakia picha ya skrini, tuambie unachotafuta, na AI yetu itakuonyesha kipande husika (hii ni demo).',
        'try_label_source_url': 'URL ya Video (k.m., YouTube, Vimeo)',
        'try_label_source_upload': 'Au Pakia Picha ya Skrini/Picha',
        'try_label_query': 'Unatafuta nini kwenye video?',
        'try_button_find': 'Pata Kipande (Demo)',
        'try_trial_counter': 'Una majaribio {count} ya demo ya bure yaliyosalia.',
        'try_trial_counter_plural': 'Una majaribio {count} ya demo ya bure yaliyosalia.',
        'try_trial_limit': 'Umetumia majaribio yako yote ya demo ya bure.',
        'try_trial_subscribe': 'Jisajili kutumia Papri kamili!',
        'try_file_selected_prefix': 'Imechaguliwa: ',
        'pricing_per_month': '/ mwezi',
        'pricing_rate_disclaimer': '*Kiwango cha ubadilishaji ni cha kukadiria.',
        // ... (Translate ALL other keys for Swahili) ...
        'footer_text': `© {year} Papri. Pata matukio yako ya video, haraka zaidi.`,
    }
    // Add other languages like 'fr', 'es', etc.
};

document.addEventListener('DOMContentLoaded', () => {
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) currentYearSpan.textContent = new Date().getFullYear();

    // --- Initialize Lucide Icons ---
    if (typeof lucide !== 'undefined') lucide.createIcons();
    else console.warn('Lucide icons script not loaded.');

    // --- Mobile Menu ---
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileNavLinks = document.querySelectorAll('.nav-link-mobile');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            const isHidden = mobileMenu.classList.toggle('hidden');
            mobileMenuButton.setAttribute('aria-expanded', String(!isHidden));
            const icon = mobileMenuButton.querySelector('i');
            if (icon) { icon.setAttribute('data-lucide', isHidden ? 'menu' : 'x'); lucide.createIcons(); }
        });
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', () => {
                 mobileMenu.classList.add('hidden');
                 mobileMenuButton.setAttribute('aria-expanded', 'false');
                 const icon = mobileMenuButton.querySelector('i');
                 if (icon) { icon.setAttribute('data-lucide', 'menu'); lucide.createIcons(); }
            });
        });
    }

    // --- Smooth Scrolling for Nav Links ---
    document.querySelectorAll('header a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId.startsWith('#') && targetId.length > 1) {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    const headerOffset = document.getElementById('header')?.offsetHeight || 0;
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset - 15; // Small padding
                    window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
                }
            }
        });
    });

    // --- File Upload Display Name ---
    const fileUploadInput = document.getElementById('video-upload'); // For "Try Papri" section
    const fileNameDisplay = document.getElementById('file-name-display');
    const videoUrlInputLanding = document.getElementById('video-url'); // Landing page URL input

    if (fileUploadInput && fileNameDisplay) {
        const prefixText = fileNameDisplay.dataset.prefixText || "Selected: ";
        fileUploadInput.addEventListener('change', () => {
            if (fileUploadInput.files.length > 0) {
                fileNameDisplay.textContent = `${prefixText}${fileUploadInput.files[0].name}`;
                if (videoUrlInputLanding) videoUrlInputLanding.value = ''; // Clear URL if file selected
            } else {
                fileNameDisplay.textContent = '';
            }
        });
    }
    if (videoUrlInputLanding && fileUploadInput && fileNameDisplay) {
        videoUrlInputLanding.addEventListener('input', () => {
            if(videoUrlInputLanding.value.trim() !== '') {
                if (fileUploadInput.value) fileUploadInput.value = ''; // Clear file input only if a file was selected
                fileNameDisplay.textContent = '';
            }
        });
     }

    // --- FAQ Accordion Icon Toggle ---
    document.querySelectorAll('.faq-item summary').forEach(summary => {
        summary.addEventListener('click', (e) => {
            const detailElement = summary.parentElement;
            // Toggle happens before this event sometimes, check current state *after* default action might occur
            // Or, preventDefault and manage open attribute manually. Simpler: let default happen.
            setTimeout(() => {
                const isOpen = detailElement.hasAttribute('open');
                const iconOpen = summary.querySelector('.icon-open');
                const iconClose = summary.querySelector('.icon-close');
                if (iconOpen) iconOpen.classList.toggle('hidden', isOpen);
                if (iconClose) iconClose.classList.toggle('hidden', !isOpen);
            }, 0);
        });
        // Set initial icon state
        const detailElement = summary.parentElement;
        const isOpen = detailElement.hasAttribute('open');
        const iconOpen = summary.querySelector('.icon-open');
        const iconClose = summary.querySelector('.icon-close');
        if (iconOpen) iconOpen.classList.toggle('hidden', isOpen);
        if (iconClose) iconClose.classList.toggle('hidden', !isOpen);
    });


    // --- "Try Papri" Form Simulation (Landing Page) ---
    const landingSearchForm = document.getElementById('search-form'); // In "Try Papri" section
    const landingSearchSubmitButton = document.getElementById('search-submit-button');
    const landingResultsArea = document.getElementById('search-results-area');
    const landingResultsContainer = document.getElementById('search-results-container');
    const landingLoadingIndicator = document.getElementById('search-in-progress');
    const landingErrorIndicator = document.getElementById('search-error');
    const landingNoResultsIndicator = document.getElementById('no-results');

    const trialCounterDisplay = document.getElementById('trial-counter');
    const trialLimitMessage = document.getElementById('trial-limit-message');
    const trialCookieName = 'papri_landing_trial_count';
    const maxTrials = 3;

    const getTrialCookie = (name) => { /* ... (same as your getCookie) ... */ 
        const value = `; ${document.cookie}`; const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift(); return null;
    };
    const setTrialCookie = (name, value, days = 7) => { /* ... (same as your setCookie) ... */
        let expires = ""; if (days) { const date = new Date(); date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000)); expires = "; expires=" + date.toUTCString(); }
        document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
    };

    let currentLandingTrials = parseInt(getTrialCookie(trialCookieName));
    if (isNaN(currentLandingTrials) || currentLandingTrials < 0) {
        currentLandingTrials = maxTrials;
        setTrialCookie(trialCookieName, currentLandingTrials);
    }

    const updateLandingTrialDisplay = (count, lang) => {
        if (trialCounterDisplay) {
            const transSet = translations[lang] || translations['en'];
            let key = 'try_trial_counter';
            if (count !== 1 && transSet['try_trial_counter_plural']) key = 'try_trial_counter_plural';
            let text = transSet[key] || (count === 1 ? "You have {count} free demo search remaining." : "You have {count} free demo searches remaining.");
            trialCounterDisplay.innerHTML = text.replace('{count}', `<strong>${count}</strong>`);
        }
    };

    const disableLandingSearch = (lang) => {
        if (landingSearchForm) landingSearchForm.querySelectorAll('input, textarea, button').forEach(el => el.disabled = true);
        if (landingSearchSubmitButton) landingSearchSubmitButton.disabled = true;
        if (trialCounterDisplay) trialCounterDisplay.classList.add('hidden');
        if (trialLimitMessage) {
            trialLimitMessage.classList.remove('hidden');
            // Ensure limit message is also translated
            const transSet = translations[lang] || translations['en'];
            trialLimitMessage.querySelector('p').textContent = transSet['try_trial_limit'] || "You've used all your free demo searches.";
            trialLimitMessage.querySelector('a').textContent = transSet['try_trial_subscribe'] || "Sign Up to search with the full Papri app!";
        }
    };
    
    // Initial state for trial counter
    const currentLangForTrials = document.documentElement.lang || 'en';
    if (currentLandingTrials <= 0) {
        disableLandingSearch(currentLangForTrials);
    } else {
        updateLandingTrialDisplay(currentLandingTrials, currentLangForTrials);
        if (trialLimitMessage) trialLimitMessage.classList.add('hidden');
    }

    if (landingSearchForm) {
        landingSearchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            currentLandingTrials = parseInt(getTrialCookie(trialCookieName)) || 0;
            const lang = document.documentElement.lang || 'en';

            if (currentLandingTrials <= 0) {
                disableLandingSearch(lang);
                alert(translations[lang]?.['try_trial_limit'] || "No demo searches remaining. Please sign up!");
                return;
            }

            currentLandingTrials--;
            setTrialCookie(trialCookieName, currentLandingTrials);
            updateLandingTrialDisplay(currentLandingTrials, lang);

            if (landingResultsArea) landingResultsArea.classList.remove('hidden');
            if (landingResultsContainer) landingResultsContainer.innerHTML = '';
            if (landingLoadingIndicator) landingLoadingIndicator.classList.remove('hidden');
            if (landingErrorIndicator) landingErrorIndicator.classList.add('hidden');
            if (landingNoResultsIndicator) landingNoResultsIndicator.classList.add('hidden');
            if (landingSearchSubmitButton) landingSearchSubmitButton.disabled = true;

            // Simulate search delay and results for landing page demo
            setTimeout(() => {
                if (landingLoadingIndicator) landingLoadingIndicator.classList.add('hidden');
                if (landingSearchSubmitButton && currentLandingTrials > 0) landingSearchSubmitButton.disabled = false;
                else if (currentLandingTrials <=0) disableLandingSearch(lang);


                const query = document.getElementById('search-query')?.value.toLowerCase() || "";
                let mockResults = [];
                if (query.includes("cat") || query.includes("paka")) {
                    mockResults = [
                        { time: "00:12 - 00:18", text: "Simulated: Cute cat playing with yarn.", source: "Demo Video 1" },
                        { time: "00:45 - 00:52", text: "Simulated: Cat jumps and misses the counter.", source: "Demo Video 2" },
                    ];
                } else if (query) {
                     mockResults = [
                        { time: "01:05 - 01:15", text: `Simulated: Found a relevant segment about "${query.split(" ")[0]}" in a demo.`, source: "General Demo Content" }
                    ];
                } else { // No query, but maybe image was uploaded
                     mockResults = [
                        { time: "00:30 - 00:35", text: "Simulated: Visual match found in a cooking demo video.", source: "Demo Visual Search"}
                     ]
                }

                if (mockResults.length > 0 && landingResultsContainer) {
                    mockResults.forEach(result => {
                        const resultElement = document.createElement('div');
                        resultElement.className = 'bg-white p-4 rounded-lg shadow border border-slate-200 animate-fade-in-item';
                        resultElement.innerHTML = `
                            <p class="text-sm text-slate-600">Demo match at: <span class="font-medium text-indigo-700">${result.time}</span> (Source: ${result.source})</p>
                            <p class="mt-1 text-base text-slate-800">"${result.text}"</p>
                            <div class="mt-3">
                                <a href="{% provider_login_url 'google' process='login' next='/app/' %}" class="text-xs inline-flex items-center px-2.5 py-1 rounded border border-indigo-500 text-indigo-600 hover:bg-indigo-50 transition-colors">
                                    <i data-lucide="arrow-right-circle" class="w-3.5 h-3.5 mr-1.5"></i> See in Full App (Sign Up)
                                </a>
                            </div>`;
                        landingResultsContainer.appendChild(resultElement);
                    });
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                } else {
                    if (landingNoResultsIndicator) landingNoResultsIndicator.classList.remove('hidden');
                }
                if (currentLandingTrials <= 0) disableLandingSearch(lang);
            }, 1500 + Math.random() * 500);
        });
    }

    // --- Localization and Currency ---
    const translationsCache = {}; // Simple cache for fetched currency rates

    async function getExchangeRate(baseCurrency, targetCurrency) {
        if (baseCurrency === targetCurrency) return 1.0;
        const cacheKey = `${baseCurrency}_${targetCurrency}`;
        if (translationsCache[cacheKey] && translationsCache[cacheKey].rate && 
            (Date.now() - translationsCache[cacheKey].timestamp < 1000 * 60 * 60 * 6)) { // Cache for 6 hours
            return translationsCache[cacheKey].rate;
        }

        // Using a free, public API (ExchangeRate-API's free tier, no API key needed for base USD)
        // For other base currencies or more features, you'd need their paid plan / API key.
        // Example: https://open.er-api.com/v6/latest/USD
        // IMPORTANT: This public API might have rate limits or change. For production, use a reliable, keyed service.
        try {
            const response = await fetch(`https://open.er-api.com/v6/latest/${baseCurrency.toUpperCase()}`);
            if (!response.ok) {
                console.warn(`ExchangeRate API fetch failed for ${baseCurrency}: ${response.status}`);
                return null; // Fallback, no conversion
            }
            const data = await response.json();
            if (data.rates && data.rates[targetCurrency.toUpperCase()]) {
                const rate = data.rates[targetCurrency.toUpperCase()];
                translationsCache[cacheKey] = { rate: rate, timestamp: Date.now() };
                return rate;
            } else {
                console.warn(`Target currency ${targetCurrency} not found in rates for base ${baseCurrency}.`);
                return null;
            }
        } catch (error) {
            console.error('ExchangeRate API Error:', error);
            return null; // Fallback on error
        }
    }


    async function initializeLocalization() {
        const defaultLang = 'en';
        const defaultCurrency = 'USD';
        const basePriceUSDElement = document.querySelector('.price-main[data-base-price-usd]');
        const basePriceUSD = basePriceUSDElement ? parseFloat(basePriceUSDElement.dataset.basePriceUsd) : 6; // Default to 6 USD

        let lang = defaultLang;
        let targetCurrency = defaultCurrency;

        try {
            // 1. Get Geolocation (GeoJS is simple, no key needed)
            const geoResponse = await fetch('https://get.geojs.io/v1/ip/country.json');
            if (!geoResponse.ok) throw new Error(`GeoJS fetch failed: ${geoResponse.status}`);
            const geoData = await geoResponse.json();
            const countryCode = geoData.country?.toUpperCase();
            console.log('Detected Country Code:', countryCode);

            // 2. Determine Language & Currency based on country
            if (countryCode === 'KE') { // Kenya
                lang = 'sw'; // Swahili
                targetCurrency = 'KES';
            } else if (countryCode === 'FR') { // France
                lang = 'fr'; // French (assuming you add 'fr' to translations)
                targetCurrency = 'EUR';
            } else if (['DE', 'AT', 'BE', 'ES', 'FI', 'IE', 'IT', 'LU', 'NL', 'PT', 'CY', 'EE', 'GR', 'LV', 'MT', 'SI', 'SK'].includes(countryCode)) { // Eurozone
                targetCurrency = 'EUR';
                // lang could be set based on specific country if translations exist
            } else if (countryCode === 'GB') { // UK
                targetCurrency = 'GBP';
            }
            // Add more mappings...

            // Apply Translation
            if (translations[lang]) {
                translatePage(lang);
                document.documentElement.lang = lang;
                const langMeta = document.querySelector('meta[http-equiv="Content-Language"]');
                if (langMeta) langMeta.setAttribute('content', lang);
            } else {
                translatePage(defaultLang); // Ensure default if detected lang not supported
            }
            updateLandingTrialDisplay(currentLandingTrials, lang); // Update trial counter with correct lang


            // 3. Convert Currency Display
            const exchangeRate = await getExchangeRate('USD', targetCurrency);
            const convertedPriceDisplayEl = document.getElementById('converted-price-display');

            if (exchangeRate && targetCurrency !== defaultCurrency && basePriceUSDElement && convertedPriceDisplayEl) {
                const convertedAmount = Math.ceil(basePriceUSD * exchangeRate);
                const priceMainEl = document.querySelector('.price-main');
                const priceSuffixEl = document.querySelector('.price-currency-suffix');
                
                if (priceMainEl) priceMainEl.textContent = `${targetCurrency} ${convertedAmount}`;
                // Suffix should be translated
                if (priceSuffixEl && translations[lang] && translations[lang]['pricing_per_month']) {
                     priceSuffixEl.textContent = translations[lang]['pricing_per_month'];
                } else if (priceSuffixEl) {
                     priceSuffixEl.textContent = translations[defaultLang]['pricing_per_month'];
                }

                // No need for the "converted-price-display" if main price is updated.
                // Or use it for "approx."
                // convertedPriceDisplayEl.innerHTML = `(Approx. ${targetCurrency} ${convertedAmount} <span data-translate-key="pricing_per_month">${translations[lang]?.['pricing_per_month'] || '/ month'}</span>*)`;
                // convertedPriceDisplayEl.style.display = 'block';
                const disclaimerKey = 'pricing_rate_disclaimer';
                const disclaimerText = (translations[lang]?.[disclaimerKey] || translations[defaultLang]?.[disclaimerKey] || '*Exchange rate is approximate.');
                // Add disclaimer below price
                if(!document.getElementById('price-disclaimer')) {
                    const disclaimerP = document.createElement('p');
                    disclaimerP.id = 'price-disclaimer';
                    disclaimerP.className = 'text-xs text-slate-400 mt-0.5';
                    disclaimerP.textContent = disclaimerText;
                    basePriceUSDElement.parentElement.appendChild(disclaimerP);
                } else {
                     document.getElementById('price-disclaimer').textContent = disclaimerText;
                }


            } else if (basePriceUSDElement) { // Ensure default USD price is shown
                basePriceUSDElement.textContent = `$${basePriceUSD}`;
                 const priceSuffixEl = document.querySelector('.price-currency-suffix');
                 if (priceSuffixEl && translations[lang] && translations[lang]['pricing_per_month']) {
                     priceSuffixEl.textContent = translations[lang]['pricing_per_month'];
                 } else if (priceSuffixEl) {
                     priceSuffixEl.textContent = translations[defaultLang]['pricing_per_month'];
                 }
                if (convertedPriceDisplayEl) convertedPriceDisplayEl.style.display = 'none';
            }

        } catch (error) {
            console.error('Localization/Currency Error:', error);
            translatePage(defaultLang); // Fallback to default language
            updateLandingTrialDisplay(currentLandingTrials, defaultLang);
            // Ensure USD price is shown on error
            const priceMainEl = document.querySelector('.price-main');
            const priceSuffixEl = document.querySelector('.price-currency-suffix');
            if (priceMainEl) priceMainEl.textContent = `$${basePriceUSD}`;
            if (priceSuffixEl) priceSuffixEl.textContent = translations[defaultLang]['pricing_per_month'];

        }
    }

    function translatePage(lang) {
        console.log(`Applying translations for: ${lang}`);
        const elements = document.querySelectorAll('[data-translate-key]');
        const translationSet = translations[lang] || translations['en']; // Fallback to English

        elements.forEach(el => {
            const key = el.dataset.translateKey;
            let translatedText = translationSet[key];

            if (translatedText !== undefined) {
                if (key === 'try_trial_counter' || key === 'try_trial_counter_plural' || key === 'footer_text') {
                    // These are handled by their specific update functions or need year
                    if (key === 'footer_text') {
                        translatedText = translatedText.replace('{year}', new Date().getFullYear());
                    } else {
                        return; // Skip, handled by updateLandingTrialDisplay
                    }
                }
                // Handle prefix for file name display if needed
                if(el.id === 'file-name-display' && el.dataset.prefixText){
                    // The main content of this is dynamic, only update prefix if key matches
                    // This is better handled when file name is set.
                } else {
                    el.innerHTML = translatedText; // Use innerHTML for tags like <br>
                }
            } else {
                console.warn(`Translation key "${key}" not found for lang "${lang}". Using default or existing text.`);
                 // Fallback to English if key exists there but not in current lang
                if (lang !== 'en' && translations['en'][key] !== undefined) {
                    el.innerHTML = translations['en'][key];
                }
            }
            // Translate placeholder attribute
            const placeholderKey = el.dataset.translatePlaceholderKey;
            if (placeholderKey && translationSet[placeholderKey] !== undefined) {
                el.setAttribute('placeholder', translationSet[placeholderKey]);
            } else if (placeholderKey && lang !== 'en' && translations['en'][placeholderKey] !== undefined) {
                el.setAttribute('placeholder', translations['en'][placeholderKey]);
            }
        });
        // Re-initialize Lucide icons if any text change affected them
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // --- Tooltip Functions (Simplified from papriapp.js example) ---
    const dynamicTooltipEl = document.getElementById('dynamic-tooltip'); // Assuming this ID from index.html
    let tooltipHideTimeout;
    function handleTooltipShow(e) {
        const target = e.target.closest('[aria-label]');
        if (!target || target.disabled || !dynamicTooltipEl) return;
        const label = target.getAttribute('aria-label');
        if (!label) return;

        clearTimeout(tooltipHideTimeout);
        dynamicTooltipEl.textContent = label;
        dynamicTooltipEl.classList.remove('hidden', 'opacity-0');
        positionTooltip(target, dynamicTooltipEl);
    }
    function handleTooltipHide() {
        if (!dynamicTooltipEl) return;
        tooltipHideTimeout = setTimeout(() => {
            dynamicTooltipEl.classList.add('opacity-0');
            setTimeout(() => dynamicTooltipEl.classList.add('hidden'), 150); // Hide after fade
        }, 200); // Slight delay before hiding
    }
    function positionTooltip(targetElement, tooltipElement) {
        const rect = targetElement.getBoundingClientRect();
        tooltipElement.style.left = '0px'; tooltipElement.style.top = '0px'; // Reset for measurement
        const tooltipRect = tooltipElement.getBoundingClientRect();
        let top = rect.top - tooltipRect.height - 8; // Prefer above
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        left = Math.max(5, Math.min(left, window.innerWidth - tooltipRect.width - 5));
        if (top < 5 || (top < 30 && (rect.bottom + tooltipRect.height + 8 < window.innerHeight))) { top = rect.bottom + 8; } // Display below if not enough space above
        top = Math.max(5, Math.min(top, window.innerHeight - tooltipRect.height - 5));
        tooltipElement.style.transform = `translate(${left}px, ${top + window.scrollY}px)`;
    }


    // --- Initializations ---
    initializeLocalization(); // Load translations and currency first
    // Other initializations that might depend on translated text or user state can follow
});
