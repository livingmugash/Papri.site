
// frontend/static/js/index.js

// --- Translations Dictionary ---
// (Ensure this matches ALL data-translate-key attributes in your index.html from Step 42 Corrected Final)
const translations = {
    'en': { // English (Default)
        'page_title_meta': 'Papri - Instantly Find Any Moment in Your Videos',
        'page_description_meta': 'Papri is an AI-powered video search engine that helps you find exact moments in videos using text, concepts, or screenshots. Stop scrubbing, start finding!',
        'nav_try': 'Try Papri', 'nav_why': 'Why Papri?', 'nav_how': 'How it Works', 'nav_pricing': 'Pricing', 'nav_faq': 'FAQ',
        'button_login': 'Login', 'button_signup': 'Sign Up',
        'hero_badge': 'New AI-Powered Video Search',
        'hero_title': 'Stop Searching, Start Finding. <br class="sm:hidden">#ShazamForContent!',
        'hero_subtitle': 'Instantly Access Any Moment<br class="sm:hidden"> in Any Online Video Content.',
        'hero_button_try_v2': 'Try Demo & See Features',
        'hero_button_signup_now': 'Sign Up Now',
        'demo_title': 'See Papri in Action',
        'demo_subtitle': 'Watch this short demo to understand how Papri\'s AI can revolutionize your video search experience.',
        'try_title': 'Experience Papri Now (Demo)',
        'try_subtitle': 'Enter a link or upload an image, tell us what you\'re looking for, and see a simulation of Papri\'s AI pinpointing the moment.',
        'try_label_source_url_landing': 'Video URL (e.g., YouTube, Vimeo)', // Specific ID for landing page
        'try_label_source_upload_landing': 'Or Upload Screenshot/Image', // Specific ID for landing page
        'try_label_query_landing': 'What are you looking for?', // Specific ID for landing page
        'try_button_find': 'Find Moment (Demo)',
        'try_results_title': 'Demo Results',
        'try_searching': 'Searching Demo...',
        'try_search_error': 'Something went wrong with the demo.',
        'try_no_results': 'No demo moments found.',
        'try_trial_counter': 'You have {count} free demo search remaining.',
        'try_trial_counter_plural': 'You have {count} free demo searches remaining.',
        'try_trial_limit': 'You\'ve used all your free demo searches.',
        'try_trial_subscribe_link': 'Sign Up/Login for the Full Papri App!',
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
        'auth_main_title': 'Join Papri or Log In',
        'auth_main_subtitle': 'Access the full power of AI video search. Sign up with Google or use your email.',
        'auth_signup_title_form': 'Create New Account',
        'auth_signup_subtitle_form': 'Get started with Papri Pro features.',
        'auth_signup_with_google': 'Sign Up with Google',
        'auth_or_email_signup': 'Or sign up with email',
        'auth_label_signup_code': 'Signup Code (from payment)', // For the hidden input in your form
        'auth_label_email': 'Email Address',
        'auth_label_create_password': 'Create Password',
        'auth_label_confirm_password': 'Confirm Password',
        'auth_button_signup_create_email': 'Create Account with Email',
        'auth_existing_account_prompt': 'Already have an account?',
        'auth_login_here_link': 'Log in here',
        'auth_login_title_form': 'Log In to Papri',
        'auth_login_subtitle_form': 'Access your dashboard and continue searching.',
        'auth_login_with_google': 'Log In with Google',
        'auth_or_email_login': 'Or log in with email',
        'auth_label_email_or_username': 'Email or Username',
        'auth_label_password': 'Password',
        'auth_forgot_password': 'Forgot password?',
        'auth_button_login_email': 'Log In with Email',
        'auth_no_account_prompt': 'Don\'t have an account?',
        'auth_signup_here_link': 'Sign up here',
        'faq_title': 'Frequently Asked Questions',
        'faq_q1_title': 'How accurate is the AI search?', 'faq_q1_desc_full': 'Papri uses state-of-the-art AI models (including Natural Language Processing for transcripts and Computer Vision for image analysis) trained on vast amounts of data. It analyzes transcripts, visual elements, and context to provide highly relevant results. Accuracy improves continuously as the AI learns, but complex or ambiguous queries might occasionally yield less precise results. We aim for pinpoint accuracy in most common use cases like finding specific spoken phrases or visually distinct objects/scenes.',
        'faq_q2_title': 'What video formats and sources are supported?', 'faq_q2_desc_full': 'For V1, Papri directly integrates with YouTube, Vimeo, and Dailymotion via their APIs. We are also enabling search for PeerTube instances (and other platforms) via our advanced scraping technology. You can search by providing a video URL from these platforms or let Papri search across their content. For screenshot search, common image formats like PNG, JPG, and WEBP are supported. We continuously work to expand support.',
        'faq_q4_title_v1': "How does the 'Try Papri Free (Demo)' work?", 'faq_q4_desc_v1': "The \"Try Papri Free\" section on our landing page offers a limited number of simulated AI searches (e.g., 3 searches) using a small, predefined set of demo video content. This allows you to experience the *idea* of Papri's search capabilities. The results are illustrative and not from our full live index. To access the full Papri application with its comprehensive search across multiple platforms and your own content, you'll need to sign up for an account.",
        'faq_q7_title': 'Can I cancel my Pro subscription?', 'faq_q7_desc': 'Yes, the Papri Pro plan is billed monthly, and you can cancel your subscription at any time through your account settings within the Papri application. Your access will continue until the end of the current billing period.',
        'footer_text_v1': `© {year} PapriSearch. Find your video moments, faster.`,
        'footer_privacy': 'Privacy Policy', 'footer_terms': 'Terms of Service', 'footer_contact': 'Contact Us',
    },
    'sw': { // Swahili - YOU NEED TO TRANSLATE ALL KEYS for full localization
        'page_title_meta': 'Papri - Pata Video Haraka',
        'page_description_meta': 'Papri hutumia akili bandia kukusaidia kupata sehemu husika kwenye video.',
        // ... (Many more translations from 'en' need to be added here for Swahili) ...
        'pricing_per_month': '/ kwa mwezi',
        'try_trial_counter': 'Una majaribio {count} ya demo ya bure.',
        'try_trial_counter_plural': 'Una majaribio {count} ya demo ya bure.',
        'try_trial_limit': 'Majaribio ya demo yameisha.',
        'try_trial_subscribe_link': 'Jisajili/Ingia kwa Papri kamili!',
        'footer_text_v1': `© {year} PapriSearch. Tafuta video zako, haraka zaidi.`,
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const logger = (message, type = 'log', data = null) => {
        const prefix = `[PapriLanding]`;
        if (data) console[type](`${prefix} ${message}`, data);
        else console[type](`${prefix} ${message}`);
    };

    logger("DOM fully loaded and parsed for index.html.");

    // --- Initialize Lucide Icons ---
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
        logger("Lucide icons rendered.");
    } else {
        logger('Lucide icons script not loaded.', 'warn');
    }
    
    // --- Update Dynamic Year in Footer ---
    const currentYearSpan = document.getElementById('currentYearFooter'); // ID from revised index.html
    if (currentYearSpan) currentYearSpan.textContent = new Date().getFullYear();

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
        mobileMenu.querySelectorAll('a.nav-link-mobile').forEach(link => {
            link.addEventListener('click', () => {
                 mobileMenu.classList.add('hidden');
                 mobileMenuButton.setAttribute('aria-expanded', 'false');
                 const icon = mobileMenuButton.querySelector('i');
                 if (icon) { icon.setAttribute('data-lucide', 'menu'); lucide.createIcons(); }
            });
        });
    } else {
        logger("Mobile menu elements not found.", "warn");
    }

    // --- Smooth Scrolling for Nav Links on this page ---
    document.querySelectorAll('header a[href^="#"], a.nav-link-mobile[href^="#"], #hero a[href="#try"], #pricing a[href="#auth"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId.startsWith('#') && targetId.length > 1) {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    const headerOffset = document.getElementById('header')?.offsetHeight || 64; 
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset - 20;
                    window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
                } else {
                    logger(`Smooth scroll target "${targetId}" not found.`, "warn");
                }
            }
        });
    });

    // --- File Upload Display Name (Landing Page Demo - for #landing-video-upload) ---
    const landingFileUploadInput = document.getElementById('landing-video-upload');
    const landingFileNameDisplay = document.getElementById('landing-file-name-display');
    const landingVideoUrlInput = document.getElementById('landing-video-url'); // Assumed ID for URL input in demo

    if (landingFileUploadInput && landingFileNameDisplay) {
        const defaultPrefixText = landingFileNameDisplay.dataset.prefixText || "Selected: ";
        landingFileUploadInput.addEventListener('change', () => {
            const currentLang = document.documentElement.lang || 'en';
            const prefixKey = landingFileNameDisplay.dataset.translateKey; // Should be 'try_file_selected_prefix'
            const translatedPrefix = (translations[lang]?.[prefixKey] || translations['en']?.[prefixKey] || defaultPrefixText);
            
            if (landingFileUploadInput.files.length > 0) {
                landingFileNameDisplay.textContent = `${translatedPrefix}${landingFileUploadInput.files[0].name}`;
                if (landingVideoUrlInput) landingVideoUrlInput.value = ''; // Clear URL if file is selected
            } else {
                landingFileNameDisplay.textContent = '';
            }
        });
    }
    if (landingVideoUrlInput && landingFileUploadInput && landingFileNameDisplay) { // Clear file if URL is typed
        landingVideoUrlInput.addEventListener('input', () => {
            if (landingVideoUrlInput.value.trim() !== '') {
                if(landingFileUploadInput.value) landingFileUploadInput.value = ''; // Clear file input
                landingFileNameDisplay.textContent = ''; // Clear display text
            }
        });
     }

    // --- FAQ Accordion Icon Toggle (Using group-open for Tailwind) ---
    document.querySelectorAll('details.faq-item summary.faq-summary').forEach(summary => {
        summary.addEventListener('click', () => {
            // Tailwind's group-open should handle icon visibility via CSS
            // This timeout is just to ensure Lucide re-renders if icons are complex SVGs
            setTimeout(() => { if (typeof lucide !== 'undefined') { lucide.createIcons(); } }, 0);
        });
        // Set initial icon state based on 'open' attribute
        const detailElement = summary.parentElement;
        const isOpen = detailElement.hasAttribute('open');
        const iconOpen = summary.querySelector('.icon-open');
        const iconClose = summary.querySelector('.icon-close');
        if (iconOpen) iconOpen.classList.toggle('hidden', isOpen);
        if (iconClose) iconClose.classList.toggle('hidden', !isOpen);
    });


    // --- "Try Papri" Form Simulation (Landing Page Demo for #landing-search-form) ---
    const landingSearchForm = document.getElementById('landing-search-form');
    const landingSearchSubmitButton = document.getElementById('landing-search-submit-button');
    const landingResultsArea = document.getElementById('landing-search-results-area');
    const landingResultsContainer = document.getElementById('landing-search-results-container');
    const landingLoadingIndicator = document.getElementById('landing-search-in-progress');
    const landingNoResultsIndicator = document.getElementById('landing-no-results');

    const trialCounterDisplay = document.getElementById('trial-counter');
    const trialLimitMessageContainer = document.getElementById('trial-limit-message');
    const trialCookieName = 'papri_landing_demo_trials_v1.2'; // Unique cookie name
    const maxTrials = 3;

    const getCookie = (name) => { /* ... (implementation as before) ... */ 
        const value = `; ${document.cookie}`; const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift(); return null;
    };
    const setCookie = (name, value, days = 7) => { /* ... (implementation as before, with Secure flag) ... */
        let exp = ""; if(days){const d=new Date();d.setTime(d.getTime()+(days*24*60*60*1000));exp="; expires="+d.toUTCString();}
        document.cookie = name + "=" + (value || "") + exp + "; path=/; SameSite=Lax; Secure";
    };

    let currentLandingTrials = parseInt(getCookie(trialCookieName));
    if (isNaN(currentLandingTrials) || currentLandingTrials < 0) {
        currentLandingTrials = maxTrials;
        setCookie(trialCookieName, currentLandingTrials);
    }

    const updateLandingTrialDisplay = (count, lang) => {
        if (!trialCounterDisplay) return;
        const transSet = translations[lang] || translations['en'];
        let key = count === 1 ? 'try_trial_counter' : 'try_trial_counter_plural';
        let text = transSet[key] || (count === 1 ? "You have {count} free demo search remaining." : "You have {count} free demo searches remaining.");
        trialCounterDisplay.innerHTML = text.replace('{count}', `<strong class="text-indigo-700 font-bold">${count}</strong>`);
    };

    const disableLandingSearchUI = (lang) => {
        if (landingSearchSubmitButton) landingSearchSubmitButton.disabled = true;
        if (trialCounterDisplay) trialCounterDisplay.classList.add('hidden');
        if (trialLimitMessageContainer) {
            trialLimitMessageContainer.classList.remove('hidden');
            const transSet = translations[lang] || translations['en'];
            trialLimitMessageContainer.querySelectorAll('[data-translate-key]').forEach(el => {
                const key = el.dataset.translateKey;
                if (transSet[key]) el.innerHTML = transSet[key]; // Use innerHTML for the link
            });
        }
    };
    
    function initializeTrialCounterAndMessages(lang) {
        if (currentLandingTrials <= 0) {
            disableLandingSearchUI(lang);
        } else {
            updateLandingTrialDisplay(currentLandingTrials, lang);
            if (trialLimitMessageContainer) trialLimitMessageContainer.classList.add('hidden');
            if (landingSearchSubmitButton) landingSearchSubmitButton.disabled = false;
        }
        if (landingFileNameDisplay) { // Translate prefix for file name
            const prefixKey = landingFileNameDisplay.dataset.translateKey; // try_file_selected_prefix
            if (prefixKey) {
                landingFileNameDisplay.dataset.prefixText = (translations[lang]?.[prefixKey] || translations['en']?.[prefixKey] || "Selected: ");
            }
        }
    }

    if (landingSearchForm) {
        landingSearchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const lang = document.documentElement.lang || 'en';
            currentLandingTrials = parseInt(getCookie(trialCookieName)) || 0;

            if (currentLandingTrials <= 0) {
                disableLandingSearchUI(lang);
                const limitText = (translations[lang] || translations['en'])['try_trial_limit'] || "No demo searches.";
                alert(limitText); // Simple alert for demo
                return;
            }

            currentLandingTrials--;
            setCookie(trialCookieName, currentLandingTrials);
            updateLandingTrialDisplay(currentLandingTrials, lang);

            if (landingResultsArea) landingResultsArea.classList.remove('hidden');
            if (landingResultsContainer) landingResultsContainer.innerHTML = ''; 
            if (landingLoadingIndicator) landingLoadingIndicator.classList.remove('hidden');
            if (landingNoResultsIndicator) landingNoResultsIndicator.classList.add('hidden');
            if (landingSearchSubmitButton) landingSearchSubmitButton.disabled = true;

            setTimeout(() => { 
                if (landingLoadingIndicator) landingLoadingIndicator.classList.add('hidden');
                
                const query = document.getElementById('landing-search-query')?.value.toLowerCase() || "";
                const fileUploaded = document.getElementById('landing-video-upload')?.files?.length > 0;
                let mockResults = [];
                // ... (Mock result generation logic - from Step 43, ensure it's relevant)
                if (query.includes("cat") || fileUploaded) mockResults.push({ time: "00:12 - 00:18", text: "Simulated: Cute cat playing with yarn, found from your query!", source: "Demo Video - Cats Vol. 1" });
                if (query.includes("tutorial")) mockResults.push({ time: "03:30 - 03:45", text: `Simulated: Found a Django tutorial segment about models.`, source: "Demo - Tech Tutorial" });
                if(mockResults.length === 0 && (query || fileUploaded)) mockResults.push({ time: "01:00 - 01:10", text: `Simulated: A relevant moment was found based on your input.`, source: "General Demo" });


                if (mockResults.length > 0 && landingResultsContainer) {
                    mockResults.forEach(result => {
                        const resultEl = document.createElement('div');
                        resultEl.className = 'bg-white p-4 rounded-lg shadow-md border border-slate-200 animate-fade-in-item';
                        // Use the Sign Up button's link from the header
                        const signupHeaderButton = document.querySelector('header a[data-translate-key="button_signup"]');
                        const signupUrl = signupHeaderButton ? signupHeaderButton.href : "{% url 'account_signup' %}"; // Fallback to Django tag

                        resultEl.innerHTML = `
                            <p class="text-sm text-slate-700">Demo Match: <span class="font-semibold text-indigo-600">${result.time}</span> (Source: ${result.source})</p>
                            <p class="mt-1.5 text-slate-800">"${result.text}"</p>
                            <div class="mt-3">
                                <a href="${signupUrl}" class="text-sm inline-flex items-center px-3 py-1.5 rounded-md border border-indigo-600 text-indigo-600 hover:bg-indigo-50 font-medium transition-colors">
                                    <i data-lucide="unlock" class="w-4 h-4 mr-2"></i> Unlock Full App (Sign Up/Login)
                                </a>
                            </div>`;
                        landingResultsContainer.appendChild(resultEl);
                    });
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                } else {
                    if (landingNoResultsIndicator) landingNoResultsIndicator.classList.remove('hidden');
                }
                
                if (currentLandingTrials <= 0) {
                    disableLandingSearchUI(lang);
                } else {
                    if (landingSearchSubmitButton) landingSearchSubmitButton.disabled = false;
                }
            }, 1000 + Math.random() * 300);
        });
    }

    // --- Localization and Currency Conversion ---
    const translationsCache = { rates: {}, geo: null, lastGeoFetch: 0 }; // Reset cache or make it more robust

    async function getGeoAndLang() { /* ... (implementation from Step 43, ensure logger is used) ... */
        const GEO_CACHE_DURATION = 1000*60*60*12; if(translationsCache.geo && (Date.now()-translationsCache.lastGeoFetch < GEO_CACHE_DURATION)) return translationsCache.geo;
        try {
            const r = await fetch('https://get.geojs.io/v1/ip/geo.json'); if(!r.ok) throw new Error(`GeoJS ${r.status}`); const d = await r.json();
            translationsCache.geo = {country_code:d.country_code?.toUpperCase(),language:(d.language_code||'en').split('-')[0],currency:d.currency_code||'USD',timezone:d.timezone};
            translationsCache.lastGeoFetch = Date.now();
            if(d.country_code === 'KE'){translationsCache.geo.language='sw';translationsCache.geo.currency='KES';}
            else if (d.country_code === 'FR') { translationsCache.geo.language = 'fr'; translationsCache.geo.currency = 'EUR'; }
            else if (['DE', 'AT', 'ES', 'IT', 'NL', 'PT', 'BE', 'FI', 'GR', 'IE', 'LU', 'CY', 'EE', 'LV', 'MT', 'SI', 'SK'].includes(d.country_code)) {translationsCache.geo.currency = 'EUR';} 
            else if (d.country_code === 'GB') { translationsCache.geo.currency = 'GBP'; }
            logger('Detected Geo:', 'log', translationsCache.geo); return translationsCache.geo;
        } catch(e){logger('GeoIP Error:', 'error', e); return {country_code:null,language:'en',currency:'USD',timezone:'UTC'};}
    }
    async function getExchangeRate(base, target) { /* ... (implementation from Step 43) ... */ 
        if(base===target)return 1.0; const k=`${base}_${target}`; if(translationsCache.rates[k] && (Date.now()-(translationsCache.rates[k].timestamp||0)<1000*60*60*4))return translationsCache.rates[k].rate;
        try{
            const r=await fetch(`https://open.er-api.com/v6/latest/${base.toUpperCase()}`); if(!r.ok)return null; const d=await r.json();
            if(d.rates && d.rates[target.toUpperCase()]){const rate=d.rates[target.toUpperCase()]; translationsCache.rates[k]={rate,timestamp:Date.now()}; return rate;} return null;
        }catch(e){logger('ExchangeRate API Error:','error',e); return null;}
    }

    async function applyLocalizationAndCurrency() {
        const geo = await getGeoAndLang();
        const lang = (translations[geo.language]) ? geo.language : 'en';
        const targetCurrency = geo.currency || 'USD';
        
        translatePage(lang);
        document.documentElement.lang = lang;
        const langMeta = document.querySelector('meta[http-equiv="Content-Language"]');
        if (langMeta) langMeta.setAttribute('content', lang);
        
        const titleMeta = document.querySelector('meta[data-translate-key="page_title_meta"]');
        if (titleMeta && titleMeta.content) document.title = titleMeta.content;
        const descMeta = document.querySelector('meta[name="description"]');
        const descMetaContent = document.querySelector('meta[data-translate-key="page_description_meta"]');
        if(descMeta && descMetaContent && descMetaContent.content) descMeta.content = descMetaContent.content;

        initializeTrialCounterAndMessages(lang);

        // Currency Display in Pricing Section
        const priceMainEl = document.querySelector('.price-main[data-base-price-usd]');
        if (priceMainEl) {
            const basePriceUSD = parseFloat(priceMainEl.dataset.basePriceUsd) || 6;
            let finalPrice = basePriceUSD; let finalCurrency = 'USD'; let finalSymbol = '$';

            if (targetCurrency !== 'USD') {
                const rate = await getExchangeRate('USD', targetCurrency);
                if (rate) { 
                    finalPrice = Math.ceil(basePriceUSD * rate); finalCurrency = targetCurrency; 
                    const symbols = {'EUR': '€', 'GBP': '£', 'KES': 'KES '}; // Add more as needed
                    finalSymbol = symbols[targetCurrency] || targetCurrency + " ";
                }
            }
            priceMainEl.textContent = `${finalSymbol}${finalPrice}`;
            const suffixEl = priceMainEl.nextElementSibling; 
            if (suffixEl && suffixEl.dataset.translateKey === 'pricing_per_month') {
                suffixEl.textContent = (translations[lang] || translations['en'])['pricing_per_month'] || '/ month';
            }
            
            // Update or create disclaimer
            const disclaimerElId = 'price-disclaimer';
            let disclaimerEl = document.getElementById(disclaimerElId);
            if(!disclaimerEl && priceMainEl.parentElement.parentElement) { // Check parentElement exists before trying to append to its parent
                const p = document.createElement('p'); p.id = disclaimerElId; 
                p.className = 'text-xs text-slate-500 mt-1 text-center'; // Centered disclaimer
                priceMainEl.parentElement.parentElement.appendChild(p); // Append to parent of price display div
                disclaimerEl = p;
            }
            if(disclaimerEl) disclaimerEl.textContent = (translations[lang] || translations['en'])['pricing_rate_disclaimer'] || '*Exchange rates approximate. Final charge by provider.';
        }
    }

    function translatePage(lang) { /* ... (Implementation from Step 43) ... */
        logger(`Applying translations for lang: ${lang}`);
        const elements = document.querySelectorAll('[data-translate-key]');
        const transSet = translations[lang] || translations['en'];
        elements.forEach(el => {
            const key = el.dataset.translateKey; let txt = transSet[key];
            if (txt !== undefined) {
                if (key==='try_trial_counter'||key==='try_trial_counter_plural')return;
                if (key==='footer_text_v1') txt = txt.replace('{year}',new Date().getFullYear());
                if (el.tagName==='META') el.content=txt; else el.innerHTML=txt;
            } else {
                if (lang !== 'en' && translations['en'][key] !== undefined) {
                    let fbTxt = translations['en'][key]; if(key==='footer_text_v1')fbTxt=fbTxt.replace('{year}',new Date().getFullYear());
                    if(el.tagName==='META')el.content=fbTxt;else el.innerHTML=fbTxt;
                } else { logger(`TransKey "${key}" missing for lang "${lang}".`, 'warn');}
            }
            const phKey=el.dataset.translatePlaceholderKey;
            if(phKey&&transSet[phKey]!==undefined)el.setAttribute('placeholder',transSet[phKey]);
            else if(phKey&&lang!=='en'&&translations['en'][phKey]!==undefined)el.setAttribute('placeholder',translations['en'][phKey]);
            if(el.id==='landing-file-name-display'&&key==='try_file_selected_prefix')el.dataset.prefixText=txt||"Selected: ";
        });
        if(typeof lucide!=='undefined')lucide.createIcons();
    }

    // Tooltip functions (ensure #dynamic-tooltip div exists in index.html)
    // ... (Tooltip functions handleTooltipShow, handleTooltipHide, positionTooltip from Step 43) ...
    const dynamicTooltipEl = document.getElementById('dynamic-tooltip');
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
        dynamicTooltipEl.classList.add('opacity-100'); // Make visible after positioning
    }

    function handleTooltipHide() {
        if (!dynamicTooltipEl) return;
        tooltipHideTimeout = setTimeout(() => {
            dynamicTooltipEl.classList.remove('opacity-100');
            dynamicTooltipEl.classList.add('opacity-0');
            // Wait for transition to finish before adding 'hidden'
            setTimeout(() => {
                if (!dynamicTooltipEl.classList.contains('opacity-100')) { // Check if it wasn't re-shown
                    dynamicTooltipEl.classList.add('hidden');
                }
            }, 150); // Match transition duration in CSS if any
        }, 100); // Shorter delay before starting to hide
    }

    function positionTooltip(targetElement, tooltipElement) {
        const rect = targetElement.getBoundingClientRect();
        tooltipElement.style.transform = ''; // Reset transform before measuring
        const tooltipRect = tooltipElement.getBoundingClientRect();
        
        let top = rect.top - tooltipRect.height - 10; // 10px offset from element
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);

        // Boundary checks
        left = Math.max(8, Math.min(left, window.innerWidth - tooltipRect.width - 8));
        if (top < 8) { // If not enough space above, try below
            top = rect.bottom + 10;
            if (top + tooltipRect.height > window.innerHeight - 8) { // If still no space, adjust
                top = window.innerHeight - tooltipRect.height - 8;
            }
        }
        tooltipElement.style.transform = `translate(${Math.round(left)}px, ${Math.round(top + window.scrollY)}px)`;
    }
    
    if (dynamicTooltipEl) {
        document.body.addEventListener('mouseover', handleTooltipShow);
        document.body.addEventListener('mouseout', handleTooltipHide);
        document.body.addEventListener('focusin', handleTooltipShow);
        document.body.addEventListener('focusout', handleTooltipHide);
    } else {
        logger("Dynamic tooltip element (#dynamic-tooltip) not found in HTML.", "warn");
    }


    // --- Initialize Landing Page ---
    applyLocalizationAndCurrency(); 
    logger("Landing page fully initialized.");
});
