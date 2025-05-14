// frontend/static/js/index.js (snippet for currency conversion update)
function convertCurrencyDisplay(basePriceUSD, targetCurrency, exchangeRate, lang) {
    const localizations = translations[lang] || translations['en'];
    const perMonthText = localizations['pricing_per_month'] || '/ month';

    const convertedAmount = Math.ceil(basePriceUSD * exchangeRate);

    // Update main price display ($6 plan)
    const proPlanPriceElement = document.querySelector('#pricing .text-5xl'); // Target the $6 specifically
    if (proPlanPriceElement && targetCurrency !== 'USD') {
        proPlanPriceElement.textContent = `${targetCurrency} ${convertedAmount}`;
        const perMonthSpan = proPlanPriceElement.nextElementSibling;
        if(perMonthSpan) perMonthSpan.textContent = perMonthText;
    } else if (proPlanPriceElement) {
         proPlanPriceElement.textContent = `$${basePriceUSD}`; // Ensure USD is shown if no conversion
         const perMonthSpan = proPlanPriceElement.nextElementSibling;
         if(perMonthSpan) perMonthSpan.textContent = perMonthText;
    }


    // Update M-Pesa amount display
    const mpesaAmountDisplay = document.querySelector('.mpesa-amount-display');
    if (mpesaAmountDisplay) {
        mpesaAmountDisplay.innerHTML = `<span class="math-inline">\{targetCurrency\} <strong\></span>{convertedAmount}</strong>`;
    }

    // Update Bank Transfer amount display
    const bankAmountDisplayLocal = document.getElementById('bank-local-amount');
    if (bankAmountDisplayLocal) {
        bankAmountDisplayLocal.textContent = `(approx. ${targetCurrency} ${convertedAmount})`;
    }
    const bankAmountUSD = document.getElementById('bank-usd-amount');
    if (bankAmountUSD) {
        bankAmountUSD.textContent = `$${basePriceUSD} USD`;
    }


    // Update "Pay Securely" buttons
    const paymentSubmitButtons = document.querySelectorAll('.payment-submit-button');
    const payButtonBaseText = localizations['payment_button_pay'] || 'Pay';
    const securelyText = localizations['payment_button_securely'] || 'Securely';

    paymentSubmitButtons.forEach(button => {
        if (targetCurrency === 'USD') {
            button.textContent = `${payButtonBaseText} $${basePriceUSD} ${securelyText}`;
        } else {
            button.textContent = `${payButtonBaseText} ${targetCurrency} ${convertedAmount} ${securelyText}`;
        }
         // For flutterwave button, might need to handle the icon differently if text changes too much
        if (button.dataset.method === 'flutterwave') {
            const flutterwaveImg = button.querySelector('img');
            button.textContent = ''; // Clear existing text
            if (flutterwaveImg) button.appendChild(flutterwaveImg); // Re-add image
             const flutterwaveTextKey = 'payment_button_with_flutterwave';
             let flutterwavePayText = localizations[flutterwaveTextKey] || `Pay ${targetCurrency} ${convertedAmount} with Flutterwave`;
             flutterwavePayText = flutterwavePayText.replace('ZZZ', `${targetCurrency} ${convertedAmount}`); // If ZZZ was a placeholder
            button.appendChild(document.createTextNode(` ${flutterwavePayText}`));
        }
    });

    // Update currency input hidden field for backend
    const currencyInput = document.querySelector('input[name="currency"]');
    if (currencyInput) {
        currencyInput.value = targetCurrency.toLowerCase();
    }
    const amountInput = document.querySelector('input[name="amount"]'); // This should be in cents or smallest unit
    if (amountInput) {
        amountInput.value = targetCurrency === 'USD' ? basePriceUSD * 100 : convertedAmount * 100;
    }
}

// Inside initializeLocalization, after getting targetCurrency and exchangeRate:
// ...
if (requiresConversion) {
    console.log(`Converting currency to: ${targetCurrency} at rate ${exchangeRate} for lang ${lang}`);
    convertCurrencyDisplay(basePriceUSD, targetCurrency, exchangeRate, lang);
} else {
    console.log(`Using default currency: USD for lang ${lang}`);
    convertCurrencyDisplay(basePriceUSD, defaultCurrency, defaultRate, lang); // Ensure default is set with lang
}
// ...
// AFTER ALL DOM MANIPULATIONS, if translations were applied, re-run to ensure texts are correct
if (lang !== defaultLang && translations[lang]) {
    translatePage(lang);
}


// frontend/static/js/index.js (Stripe specific snippet within DOMContentLoaded)
const stripePublishableKey = document.getElementById('payment-form')?.dataset.stripePk; // Add data-stripe-pk="YOUR_KEY" to your form
let stripe, cardElement;

if (stripePublishableKey) {
    stripe = Stripe(stripePublishableKey);
    const elements = stripe.elements();
    cardElement = elements.create('card', { /* style options */ });
    const cardElementMount = document.getElementById('card-element');
    if (cardElementMount) {
         cardElement.mount('#card-element');
         cardElement.on('change', function(event) {
            const displayError = document.getElementById('card-errors');
            if (event.error) {
                displayError.textContent = event.error.message;
            } else {
                displayError.textContent = '';
            }
        });
    } else {
        console.warn('Stripe card element mount point not found');
    }
} else {
    console.warn('Stripe publishable key not found on payment form.');
    // Disable card payment tab if stripe key isn't available
    const cardTab = document.querySelector('.payment-tab[data-payment-method="card"]');
    if(cardTab) cardTab.style.display = 'none';
    const cardArea = document.getElementById('payment-card-area');
    if(cardArea) cardArea.style.display = 'none';
}

// Inside paymentForm submit event listener for currentPaymentMethod === 'card'
if (currentPaymentMethod === 'card') {
    if (!stripe || !cardElement) {
        throw new Error('Stripe is not initialized.');
    }
    if (paymentProcessingMessage) paymentProcessingMessage.classList.remove('hidden');

    const { paymentMethod, error } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: {
            email: emailValue,
        },
    });

    if (error) {
        throw new Error(error.message);
    } else {
        // Send paymentMethod.id and emailValue to your backend
        const response = await fetch('/payments/create-payment-intent/', { // New Django endpoint
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // Ensure you have a getCookie function for CSRF
            },
            body: JSON.stringify({
                payment_method_id: paymentMethod.id,
                email: emailValue,
                amount: document.querySelector('input[name="amount"]').value, // in cents
                currency: document.querySelector('input[name="currency"]').value,
            }),
        });
        const paymentResponse = await response.json();

        if (paymentResponse.error) {
            throw new Error(paymentResponse.error);
        } else if (paymentResponse.requires_action) {
            // Handle 3D Secure
            const { error: errorAction, paymentIntent } = await stripe.handleNextAction({
                clientSecret: paymentResponse.client_secret
            });
            if (errorAction) {
                throw new Error(errorAction.message);
            } else {
                // PaymentIntent successful after action
                console.log('PaymentIntent after action:', paymentIntent);
                // Here you would typically show a success message and generate/show the signup code
                // For demo, we'll call the existing success simulation
                success = true;
            }
        } else if (paymentResponse.success) {
            // Payment successful without further action
            success = true;
        } else {
             throw new Error('Payment processing failed on backend.');
        }
    }
}


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
// ... rest of the try-catch for payment simulation
