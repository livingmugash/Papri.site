// frontend/static/js/index.js

// --- Translations Dictionary ---
// (This should be the comprehensive translations object from Step 42)
const translations = {
    'en': { // English (Default)
        'page_title_meta': 'Papri - Instantly Find Any Moment in Your Videos', // For document.title
        'page_description_meta': 'Papri is an AI-powered video search engine that helps you find exact moments in videos using text, concepts, or screenshots. Stop scrubbing, start finding!',
        'nav_try': 'Try Papri', 'nav_why': 'Why Papri?', 'nav_how': 'How it Works', 'nav_pricing': 'Pricing', 'nav_faq': 'FAQ',
        'button_login': 'Login', 'button_signup': 'Sign Up',
        'hero_badge': 'New AI-Powered Video Search',
        'hero_title': 'Stop Searching, Start Finding. <br class="sm:hidden">#ShazamForContent!',
        'hero_subtitle': 'Instantly Access Any Moment<br class="sm:hidden"> in Any Online Video Content.',
        'hero_button_try': 'Try Papri Free (Demo)', 'hero_button_demo': 'Watch Demo',
        'demo_title': 'See Papri in Action',
        'demo_subtitle': 'Watch this short demo to understand how Papri\'s AI can revolutionize your video search experience.',
        'try_title': 'Experience Papri Now (Demo)',
        'try_subtitle': 'Enter a link or upload an image, tell us what you\'re looking for, and see a simulation of Papri\'s AI pinpointing the moment.',
        'try_label_source_url': 'Video URL (e.g., YouTube, Vimeo)',
        'try_label_source_upload': 'Or Upload Screenshot/Image',
        'try_label_query': 'What are you looking for in the video?',
        'try_button_find': 'Find Moment (Demo)',
        'try_trial_counter': 'You have {count} free demo search remaining.',
        'try_trial_counter_plural': 'You have {count} free demo searches remaining.',
        'try_trial_limit': 'You\'ve used all your free demo searches.',
        'try_trial_subscribe_link': 'Sign Up/Login for the Full Papri App!', // For the link
        'try_file_selected_prefix': 'Selected: ',
        'why_title': 'Tired of Aimlessly Scrubbing Videos?',
        'why_subtitle': 'Papri\'s AI understands your favorite video content—transcripts, visuals, and context—letting you find exactly what you need, instantly.',
        'why_feature1_title': 'Instant Pinpoint Accuracy',
        'why_feature1_desc': 'Describe what you\'re looking for—spoken words, objects, actions, scenes—and Papri takes you to the precise moment in seconds.',
        'why_feature2_title': 'Search *Inside* Your Content',
        'why_feature2_desc': 'Papri goes beyond titles. Our AI analyzes actual video content—audio transcripts, visual elements, and context—for unparalleled relevance.',
        'why_feature3_title': 'Save Time & Boost Productivity',
        'why_feature3_desc': 'Reclaim hours lost to manual searching. Essential for content creators, researchers, students, and all video professionals.',
        'steps_title': 'Get Started in 3 Simple Steps',
        'steps_step1_title': 'Provide Content', 'steps_step1_desc': 'Paste a video link or upload your image/screenshot directly into Papri.',
        'steps_step2_title': 'Describe Moment', 'steps_step2_desc': 'Tell Papri\'s AI what you\'re looking for using natural language or visual cues.',
        'steps_step3_title': 'Find Instantly', 'steps_step3_desc': 'Our AI scans and presents the exact video segments matching your query, ready to use.',
        'pricing_title': 'Ready to Unlock Full Power?',
        'pricing_subtitle': 'Go beyond the free demo and revolutionize how you interact with video content with Papri Pro.',
        'pricing_plan_badge': 'Pro Plan',
        'pricing_plan_name': 'Papri Pro',
        'pricing_plan_audience': 'For individuals, creators, and small teams.',
        'pricing_per_month': '/ month',
        'pricing_billing_info': 'Billed monthly, cancel anytime.',
        'pricing_feature_searches': 'Unlimited AI content searches',
        'pricing_feature_sources_full': 'YouTube, Vimeo, Dailymotion, PeerTube & more',
        'pricing_feature_deep_analysis_both': 'Deep Transcript & Visual Analysis',
        'pricing_feature_timestamps_accurate': 'Accurate Timestamped Results',
        'pricing_feature_multilingual': 'Multilingual Support',
        'pricing_feature_segments': 'Download & Trim Segments (Coming Soon)',
        'pricing_feature_collections': 'Personal Collections & History',
        'pricing_feature_support': 'Priority Email Support',
        'pricing_cta_button_v1': 'Sign Up & Get Papri Pro',
        'pricing_enterprise_prompt': 'Need custom features or higher limits?', 
        'pricing_contact_sales': 'Contact Sales',
        'pricing_rate_disclaimer': '*Exchange rate is approximate. Final charge processed by payment provider.',
        'faq_title': 'Frequently Asked Questions',
        'faq_q1_title': 'How accurate is the AI search?', 'faq_q1_desc_full': 'Papri uses state-of-the-art AI models (including Natural Language Processing for transcripts and Computer Vision for image analysis) trained on vast amounts of data. It analyzes transcripts, visual elements, and context to provide highly relevant results. Accuracy improves continuously as the AI learns, but complex or ambiguous queries might occasionally yield less precise results. We aim for pinpoint accuracy in most common use cases like finding specific spoken phrases or visually distinct objects/scenes.',
        'faq_q2_title': 'What video formats and sources are supported?', 'faq_q2_desc_full': 'For V1, Papri directly integrates with YouTube, Vimeo, and Dailymotion via their APIs. We are also enabling search for PeerTube instances (and other platforms) via our advanced scraping technology. You can search by providing a video URL from these platforms or let Papri search across their content. For screenshot search, common image formats like PNG, JPG, and WEBP are supported. We continuously work to expand support.',
        'faq_q4_title_v1': "How does the 'Try Papri Free (Demo)' work?", 'faq_q4_desc_v1': "The \"Try Papri Free\" section on our landing page offers a limited number of simulated AI searches (e.g., 3 searches) using a small, predefined set of demo video content. This allows you to experience the *idea* of Papri's search capabilities. The results are illustrative and not from our full live index. To access the full Papri application with its comprehensive search across multiple platforms and your own content, you'll need to sign up for an account.",
        'faq_q7_title': 'Can I cancel my Pro subscription?', 'faq_q7_desc': 'Yes, the Papri Pro plan is billed monthly, and you can cancel your subscription at any time through your account settings within the Papri application. Your access will continue until the end of the current billing period.',
        'footer_text_v1': `© {year} PapriSearch. Find your video moments, faster.`,
        'footer_privacy': 'Privacy Policy', 'footer_terms': 'Terms of Service', 'footer_contact': 'Contact Us',
    },
    'sw': { // Swahili example - YOU NEED TO TRANSLATE ALL KEYS
        'page_title_meta': 'Papri - Pata Kipande Chochote Kwenye Video Zako Mara Moja',
        'page_description_meta': 'Papri ni injini ya utafutaji video inayotumia akili bandia...',
        'nav_try': 'Jaribu Papri', 'nav_why': 'Kwa Nini Papri?', 'nav_how': 'Inavyofanya Kazi', 'nav_pricing': 'Bei', 'nav_faq': 'Maswali',
        'button_login': 'Ingia', 'button_signup': 'Jisajili',
        'hero_badge': 'Utafutaji Mpya wa Video kwa Akili Bandia',
        'hero_title': 'Acha Kutafuta, Anza Kupata. <br class="sm:hidden">#ShazamYaMaudhui!',
        'hero_subtitle': 'Fikia Kipande Chochote Mara Moja<br class="sm:hidden"> Katika Maudhui Yoyote Mtandaoni.',
        'hero_button_try': 'Jaribu Papri Bure (Demo)', 'hero_button_demo': 'Tazama Demo',
        'try_trial_counter': 'Una majaribio {count} ya demo ya bure yaliyosalia.',
        'try_trial_counter_plural': 'Una majaribio {count} ya demo ya bure yaliyosalia.',
        'try_trial_limit': 'Umetumia majaribio yako yote ya demo ya bure.',
        'try_trial_subscribe_link': 'Jisajili/Ingia kutumia Papri kamili!',
        'pricing_per_month': '/ mwezi',
        // ... many more translations needed for SW and other languages ...
        'footer_text_v1': `© {year} PapriSearch. Pata matukio yako ya video, haraka zaidi.`,
    }
    // Add other languages like 'fr', 'es', etc.
};

document.addEventListener('DOMContentLoaded', () => {
    const currentYearSpan = document.getElementById('currentYearFooter'); // Updated ID
    if (currentYearSpan) currentYearSpan.textContent = new Date().getFullYear();

    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    } else {
        console.warn('[Papri Landing] Lucide icons script not loaded.');
    }

    // --- Mobile Menu Toggle ---
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            const isHidden = mobileMenu.classList.toggle('hidden');
            mobileMenuButton.setAttribute('aria-expanded', String(!isHidden));
            const icon = mobileMenuButton.querySelector('i');
            if (icon) { icon.setAttribute('data-lucide', isHidden ? 'menu' : 'x'); lucide.createIcons(); }
        });
        // Close mobile menu when a link inside it is clicked
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.add('hidden');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
                const icon = mobileMenuButton.querySelector('i');
                if (icon) { icon.setAttribute('data-lucide', 'menu'); lucide.createIcons(); }
            });
        });
    }

    // --- Smooth Scrolling for Nav Links within the landing page ---
    document.querySelectorAll('header a[href^="#"], a.nav-link-mobile[href^="#"], a[href="#try"].w-full.sm\\:w-auto').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId.startsWith('#') && targetId.length > 1) {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    const headerOffset = document.getElementById('header')?.offsetHeight || 0;
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset - 20; // Adjusted offset
                    window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
                }
            }
        });
    });

    // --- File Upload Display Name (Landing Page Demo) ---
    const landingFileUploadInput = document.getElementById('landing-video-upload');
    const landingFileNameDisplay = document.getElementById('landing-file-name-display');
    const landingVideoUrlInput = document.getElementById('landing-video-url');

    if (landingFileUploadInput && landingFileNameDisplay) {
        const prefixTextDefault = "Selected: ";
        landingFileUploadInput.addEventListener('change', () => {
            const currentPrefix = landingFileNameDisplay.dataset.prefixText || prefixTextDefault;
            if (landingFileUploadInput.files.length > 0) {
                landingFileNameDisplay.textContent = `${currentPrefix}${landingFileUploadInput.files[0].name}`;
                if (landingVideoUrlInput) landingVideoUrlInput.value = '';
            } else {
                landingFileNameDisplay.textContent = '';
            }
        });
    }
    if (landingVideoUrlInput && landingFileUploadInput && landingFileNameDisplay) {
        landingVideoUrlInput.addEventListener('input', () => {
            if(landingVideoUrlInput.value.trim() !== '') {
                if(landingFileUploadInput.value) landingFileUploadInput.value = '';
                landingFileNameDisplay.textContent = '';
            }
        });
     }

    // --- FAQ Accordion Icon Toggle ---
    document.querySelectorAll('details.faq-item').forEach(detailElement => {
        const summary = detailElement.querySelector('summary.faq-summary');
        if (summary) {
            summary.addEventListener('click', (e) => { // No need to preventDefault for <details>
                // Icons are toggled by Tailwind's group-open utilities in the HTML
                // If you need JS to do it, you'd toggle classes here.
                // Forcing icon re-render if they are SVGs that might not update
                setTimeout(() => { if (typeof lucide !== 'undefined') lucide.createIcons(); }, 0);
            });
        }
    });

    // --- "Try Papri" Form Simulation (Landing Page Demo) ---
    const landingSearchForm = document.getElementById('landing-search-form');
    const landingSearchSubmitButton = document.getElementById('landing-search-submit-button');
    const landingResultsArea = document.getElementById('landing-search-results-area');
    const landingResultsContainer = document.getElementById('landing-search-results-container');
    const landingLoadingIndicator = document.getElementById('landing-search-in-progress');
    // const landingErrorIndicator = document.getElementById('landing-search-error'); // Not used in simple demo
    const landingNoResultsIndicator = document.getElementById('landing-no-results');

    const trialCounterDisplay = document.getElementById('trial-counter');
    const trialLimitMessageContainer = document.getElementById('trial-limit-message'); // The div container
    const trialCookieName = 'papri_landing_demo_trials';
    const maxTrials = 3;

    const getCookie = (name) => { /* ... (same as your getCookie) ... */ 
        const value = `; ${document.cookie}`; const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift(); return null;
    };
    const setCookie = (name, value, days = 7) => { /* ... (same as your setCookie) ... */
        let expires = ""; if (days) { const date = new Date(); date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000)); expires = "; expires=" + date.toUTCString(); }
        document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax; Secure"; // Added Secure
    };

    let currentLandingTrials = parseInt(getCookie(trialCookieName));
    if (isNaN(currentLandingTrials) || currentLandingTrials < 0) {
        currentLandingTrials = maxTrials;
        setCookie(trialCookieName, currentLandingTrials);
    }

    const updateLandingTrialDisplay = (count, lang) => {
        if (trialCounterDisplay) {
            const transSet = translations[lang] || translations['en'];
            let key = count === 1 ? 'try_trial_counter' : 'try_trial_counter_plural';
            let text = transSet[key] || (count === 1 ? "You have {count} free demo search remaining." : "You have {count} free demo searches remaining.");
            trialCounterDisplay.innerHTML = text.replace('{count}', `<strong class="text-indigo-700">${count}</strong>`);
        }
    };

    const disableLandingSearch = (lang) => {
        if (landingSearchForm) {
            landingSearchForm.querySelectorAll('input, textarea, button').forEach(el => {
                if (el.type === 'submit') el.disabled = true; // Only disable submit
            });
        }
        if (trialCounterDisplay) trialCounterDisplay.classList.add('hidden');
        if (trialLimitMessageContainer) {
            trialLimitMessageContainer.classList.remove('hidden');
            const transSet = translations[lang] || translations['en'];
            // Assuming the P and A tags inside trialLimitMessageContainer have the data-translate-key
            trialLimitMessageContainer.querySelectorAll('[data-translate-key]').forEach(el => {
                const key = el.dataset.translateKey;
                if (transSet[key]) el.textContent = transSet[key];
            });
        }
    };
    
    // Initial state for trial counter, called after localization
    function initializeTrialCounter(lang) {
        if (currentLandingTrials <= 0) {
            disableLandingSearch(lang);
        } else {
            updateLandingTrialDisplay(currentLandingTrials, lang);
            if (trialLimitMessageContainer) trialLimitMessageContainer.classList.add('hidden');
        }
    }


    if (landingSearchForm) {
        landingSearchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const lang = document.documentElement.lang || 'en';
            currentLandingTrials = parseInt(getCookie(trialCookieName)) || 0;

            if (currentLandingTrials <= 0) {
                disableLandingSearch(lang);
                // Optionally show an alert or more prominent message
                const limitText = (translations[lang] || translations['en'])['try_trial_limit'] || "No demo searches remaining.";
                alert(limitText + " " + (translations[lang] || translations['en'])['try_trial_subscribe_link']);
                return;
            }

            currentLandingTrials--;
            setCookie(trialCookieName, currentLandingTrials);
            updateLandingTrialDisplay(currentLandingTrials, lang);

            if (landingResultsArea) landingResultsArea.classList.remove('hidden');
            if (landingResultsContainer) landingResultsContainer.innerHTML = ''; // Clear previous demo results
            if (landingLoadingIndicator) landingLoadingIndicator.classList.remove('hidden');
            if (landingNoResultsIndicator) landingNoResultsIndicator.classList.add('hidden');
            if (landingSearchSubmitButton) landingSearchSubmitButton.disabled = true;

            setTimeout(() => { // Simulate API call
                if (landingLoadingIndicator) landingLoadingIndicator.classList.add('hidden');
                if (landingSearchSubmitButton && currentLandingTrials > 0) landingSearchSubmitButton.disabled = false;
                else if (currentLandingTrials <= 0) disableLandingSearch(lang);

                const query = document.getElementById('landing-search-query')?.value.toLowerCase() || "";
                let mockResults = [];
                // Simplified mock results logic
                if (query.includes("cat") || query.includes("paka") || query.includes("screenshot")) {
                    mockResults.push({ time: "00:12 - 00:18", text: "Simulated: Cute cat playing with yarn, found from your query!", source: "Demo Video - Cats" });
                }
                if (query.includes("tutorial") || query.includes("django")) {
                     mockResults.push({ time: "03:30 - 03:45", text: `Simulated: Found a Django tutorial segment based on "${query.split(" ")[0]}".`, source: "Demo - Tech Tutorial" });
                }
                if(mockResults.length === 0 && query) { // Generic if query but no specific match
                     mockResults.push({ time: "01:00 - 01:10", text: `Simulated: A relevant moment for "${query.split(" ")[0]}" was found.`, source: "General Demo" });
                }
                if(mockResults.length === 0 && document.getElementById('landing-video-upload')?.files?.length > 0) {
                    mockResults.push({ time: "00:05 - 00:12", text: "Simulated: Visual match found for your uploaded image in a demo reel!", source: "Demo - Visual Match Reel" });
                }


                if (mockResults.length > 0 && landingResultsContainer) {
                    mockResults.forEach(result => {
                        const resultEl = document.createElement('div');
                        resultEl.className = 'bg-white p-4 rounded-lg shadow-md border border-slate-200 animate-fade-in-item';
                        resultEl.innerHTML = `
                            <p class="text-sm text-slate-700">Demo Match: <span class="font-semibold text-indigo-600">${result.time}</span> (Source: ${result.source})</p>
                            <p class="mt-1.5 text-slate-800">"${result.text}"</p>
                            <div class="mt-3">
                                <a href="${document.querySelector('a[data-translate-key=\"button_signup\"]')?.href || '#'}" class="text-sm inline-flex items-center px-3 py-1.5 rounded-md border border-indigo-600 text-indigo-600 hover:bg-indigo-50 font-medium transition-colors">
                                    <i data-lucide="arrow-right-circle" class="w-4 h-4 mr-2"></i> Unlock Full Power (Sign Up)
                                </a>
                            </div>`;
                        landingResultsContainer.appendChild(resultEl);
                    });
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                } else {
                    if (landingNoResultsIndicator) landingNoResultsIndicator.classList.remove('hidden');
                }
                if (currentLandingTrials <= 0) disableLandingSearch(lang);
            }, 1200 + Math.random() * 400); // Simulate network delay
        });
    }

    // --- Localization and Currency Conversion ---
    const translationsCache = { rates: {}, geo: null, lastGeoFetch: 0 }; // Cache for geo-IP and rates

    async function getGeoAndLang() {
        const GEO_CACHE_DURATION = 1000 * 60 * 60 * 24; // Cache geo-IP for 24 hours
        if (translationsCache.geo && (Date.now() - translationsCache.lastGeoFetch < GEO_CACHE_DURATION)) {
            return translationsCache.geo;
        }
        try {
            const response = await fetch('https://get.geojs.io/v1/ip/country.json');
            if (!response.ok) { console.warn(`GeoJS fetch failed: ${response.status}`); return { countryCode: null, lang: 'en', currency: 'USD' }; }
            const geoData = await response.json();
            const countryCode = geoData.country?.toUpperCase();
            translationsCache.geo = { countryCode, lang: 'en', currency: 'USD' }; // Default lang/currency
            translationsCache.lastGeoFetch = Date.now();

            // Determine Language & Currency based on country
            if (countryCode === 'KE') { translationsCache.geo.lang = 'sw'; translationsCache.geo.currency = 'KES'; }
            // else if (countryCode === 'FR') { translationsCache.geo.lang = 'fr'; translationsCache.geo.currency = 'EUR'; }
            // ... Add more country to lang/currency mappings ...
            else if (['DE', 'AT', 'ES', 'IT', 'NL', 'PT', 'BE', 'FI', 'GR', 'IE', 'LU', 'CY', 'EE', 'LV', 'MT', 'SI', 'SK'].includes(countryCode)) {
                translationsCache.geo.currency = 'EUR';
                // Could set language based on specific Eurozone country if needed
            } else if (countryCode === 'GB') { translationsCache.geo.currency = 'GBP'; }
            
            console.log('[Papri Landing] Detected Geo:', translationsCache.geo);
            return translationsCache.geo;
        } catch (error) {
            console.error('[Papri Landing] GeoIP Error:', error);
            return { countryCode: null, lang: 'en', currency: 'USD' }; // Fallback
        }
    }

    async function getExchangeRate(baseCurrency, targetCurrency) {
        // ... (Implementation from Step 42, using translationsCache.rates) ...
        if (baseCurrency === targetCurrency) return 1.0;
        const cacheKey = `${baseCurrency}_${targetCurrency}`;
        if (translationsCache.rates[cacheKey] && (Date.now() - (translationsCache.rates[cacheKey].timestamp || 0) < 1000 * 60 * 60 * 4)) { // Cache for 4 hours
            return translationsCache.rates[cacheKey].rate;
        }
        try {
            const response = await fetch(`https://open.er-api.com/v6/latest/${baseCurrency.toUpperCase()}`);
            if (!response.ok) { console.warn(`ExchangeRate API failed for ${baseCurrency}: ${response.status}`); return null; }
            const data = await response.json();
            if (data.rates && data.rates[targetCurrency.toUpperCase()]) {
                const rate = data.rates[targetCurrency.toUpperCase()];
                translationsCache.rates[cacheKey] = { rate: rate, timestamp: Date.now() };
                return rate;
            } else { console.warn(`${targetCurrency} not in rates for ${baseCurrency}.`); return null; }
        } catch (error) { console.error('ExchangeRate API Error:', error); return null; }
    }

    async function applyLocalizationAndCurrency() {
        const geo = await getGeoAndLang();
        const lang = (translations[geo.lang]) ? geo.lang : 'en'; // Fallback to 'en' if detected lang not in our dict
        const targetCurrency = geo.currency;
        const defaultCurrency = 'USD';
        
        translatePage(lang); // Apply text translations
        document.documentElement.lang = lang;
        const langMeta = document.querySelector('meta[http-equiv="Content-Language"]');
        if (langMeta) langMeta.setAttribute('content', lang);
        const titleMeta = document.querySelector('meta[data-translate-key="page_title_meta"]');
        if (titleMeta) document.title = titleMeta.content; // Set page title after translation

        initializeTrialCounter(lang); // Update trial counter text with correct language

        // Currency Conversion for Pricing Section
        const priceMainEl = document.querySelector('.price-main[data-base-price-usd]');
        const priceSuffixEl = document.querySelector('.price-currency-suffix');
        const convertedPriceDisplayEl = document.getElementById('converted-price-display'); // For "approx" text

        if (!priceMainEl) return; // No pricing section to update

        const basePriceUSD = parseFloat(priceMainEl.dataset.basePriceUsd) || 6;
        let finalDisplayPrice = basePriceUSD;
        let finalDisplayCurrency = defaultCurrency;

        if (targetCurrency !== defaultCurrency) {
            const exchangeRate = await getExchangeRate('USD', targetCurrency);
            if (exchangeRate) {
                finalDisplayPrice = Math.ceil(basePriceUSD * exchangeRate);
                finalDisplayCurrency = targetCurrency;
            }
        }
        
        priceMainEl.textContent = `${finalDisplayCurrency === 'USD' ? '$' : (finalDisplayCurrency === 'EUR' ? '€' : finalDisplayCurrency)} ${finalDisplayPrice}`;
        const transSet = translations[lang] || translations['en'];
        if (priceSuffixEl) priceSuffixEl.textContent = transSet['pricing_per_month'] || '/ month';

        if (targetCurrency !== defaultCurrency && convertedPriceDisplayEl) {
            // Show original USD price as well for clarity
            convertedPriceDisplayEl.innerHTML = `(Approx. $${basePriceUSD} USD <span data-translate-key="pricing_per_month">${transSet['pricing_per_month']}</span>*)`;
            convertedPriceDisplayEl.style.display = 'block';
        } else if (convertedPriceDisplayEl) {
            convertedPriceDisplayEl.style.display = 'none';
        }
        const disclaimerEl = document.getElementById('price-disclaimer');
        if(!disclaimerEl && priceMainEl.parentElement) { // Create if not exists
            const p = document.createElement('p'); p.id = 'price-disclaimer'; p.className = 'text-xs text-slate-400 mt-0.5';
            priceMainEl.parentElement.appendChild(p);
        }
        if(document.getElementById('price-disclaimer')) document.getElementById('price-disclaimer').textContent = transSet['pricing_rate_disclaimer'] || '*Exchange rates are approximate.';

    }

    function translatePage(lang) {
        const elements = document.querySelectorAll('[data-translate-key]');
        const translationSet = translations[lang] || translations['en']; // Fallback
        elements.forEach(el => {
            const key = el.dataset.translateKey;
            let translatedText = translationSet[key];
            if (translatedText !== undefined) {
                if (key === 'try_trial_counter' || key === 'try_trial_counter_plural') { return; } // Handled separately
                if (key === 'footer_text_v1') { translatedText = translatedText.replace('{year}', new Date().getFullYear()); }
                
                // For meta tags, update their content attribute
                if (el.tagName === 'META' && el.dataset.translateKey) {
                    el.content = translatedText;
                } else {
                    el.innerHTML = translatedText; // Allows <br> etc.
                }
            } else {
                // Fallback to English if key exists there but not in current lang
                if (lang !== 'en' && translations['en'][key] !== undefined) {
                    let fallbackText = translations['en'][key];
                    if (key === 'footer_text_v1') { fallbackText = fallbackText.replace('{year}', new Date().getFullYear()); }
                    if (el.tagName === 'META') el.content = fallbackText; else el.innerHTML = fallbackText;
                } else {
                    console.warn(`[Papri Landing] TransKey "${key}" not found for lang "${lang}" or default 'en'.`);
                }
            }
            // Translate placeholder attribute
            const placeholderKey = el.dataset.translatePlaceholderKey;
            if (placeholderKey && translationSet[placeholderKey] !== undefined) {
                el.setAttribute('placeholder', translationSet[placeholderKey]);
            } else if (placeholderKey && lang !== 'en' && translations['en'][placeholderKey] !== undefined) {
                el.setAttribute('placeholder', translations['en'][placeholderKey]);
            }
            // Translate prefix for file name display
            if (el.id === 'landing-file-name-display' && key === 'try_file_selected_prefix') {
                el.dataset.prefixText = translatedText; // Store for use when file changes
            }
        });
        if (typeof lucide !== 'undefined') lucide.createIcons(); // Re-render icons if text changes affect them
    }

    // Tooltip functions (simplified, as in Step 42)
    const dynamicTooltipEl = document.getElementById('dynamic-tooltip');
    let tooltipHideTimeout;
    function handleTooltipShow(e) { /* ... */ }
    function handleTooltipHide() { /* ... */ }
    function positionTooltip(target, tooltip) { /* ... */ }
    document.body.addEventListener('mouseover', handleTooltipShow);
    document.body.addEventListener('mouseout', handleTooltipHide);


    // --- Initialize Landing Page ---
    applyLocalizationAndCurrency(); // This now handles translation and currency updates.
    
});
