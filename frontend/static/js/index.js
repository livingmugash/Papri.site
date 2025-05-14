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
