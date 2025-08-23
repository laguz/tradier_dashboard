document.addEventListener('DOMContentLoaded', function () {
    const stockOrderForm = {
        init() {
            this.orderTypeSelect = document.getElementById('stock-order_type');
            if (!this.orderTypeSelect) return;

            this.limitPriceDiv = document.getElementById('stock_limit_price_div');
            this.stopPriceDiv = document.getElementById('stock_stop_price_div');

            this.orderTypeSelect.addEventListener('change', () => this.togglePriceFields());
            this.togglePriceFields();
        },
        togglePriceFields() {
            const selectedType = this.orderTypeSelect.value;
            this.limitPriceDiv.style.display = ['limit', 'stop_limit'].includes(selectedType) ? 'block' : 'none';
            this.stopPriceDiv.style.display = ['stop', 'stop_limit'].includes(selectedType) ? 'block' : 'none';
        }
    };
    stockOrderForm.init();

    const api = {
        async fetch(url) {
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                console.error("API fetch error:", error);
                return { error: error.message };
            }
        },
        getExpirations(symbol) {
            return this.fetch(`/get_expirations/${symbol}`);
        },
        getStrikes(symbol, expiration) {
            return this.fetch(`/get_strikes/${symbol}/${expiration}`);
        }
    };

    class TradeForm {
        constructor(prefix) {
            this.prefix = prefix;
            this.symbolInput = document.getElementById(`${prefix}-underlying_symbol`);
            this.expirationSelect = document.getElementById(`${prefix}-expiration_date`);
            this.strikeSelect = document.getElementById(`${prefix}-strike`);
            this.fetchBtn = document.getElementById(`${prefix}-fetch-expirations-btn`);
        }

        init() {
            if (this.fetchBtn) {
                this.fetchBtn.addEventListener('click', () => this.fetchExpirations());
            }
            if (this.expirationSelect && this.strikeSelect) {
                this.expirationSelect.addEventListener('change', () => this.fetchStrikes());
            }
        }

        async fetchExpirations() {
            const symbol = this.symbolInput.value.trim().toUpperCase();
            if (!symbol) {
                alert('Please enter an underlying symbol first.');
                return;
            }
            this.updateSelect(this.expirationSelect, [], 'Loading...', true);
            const data = await api.getExpirations(symbol);
            const options = data.dates || [];
            const message = data.error ? data.error : (options.length > 0 ? '-- Select an Expiration --' : 'No dates found');
            this.updateSelect(this.expirationSelect, options, message, false);
        }

        async fetchStrikes() {
            const symbol = this.symbolInput.value.trim().toUpperCase();
            const expiration = this.expirationSelect.value;
            if (!symbol || !expiration) {
                this.updateSelect(this.strikeSelect, [], '-- Select Expiration --', true);
                return;
            }
            this.updateSelect(this.strikeSelect, [], 'Loading Strikes...', true);
            const data = await api.getStrikes(symbol, expiration);
            const options = data.strikes || [];
            const message = data.error ? data.error : (options.length > 0 ? '-- Select a Strike --' : 'No strikes found');
            this.updateSelect(this.strikeSelect, options, message, false);
        }

        updateSelect(selectElement, options, defaultText, isDisabled) {
            if (!selectElement) return;
            selectElement.innerHTML = `<option value="">${defaultText}</option>`;
            options.forEach(optionValue => {
                const option = document.createElement('option');
                option.value = optionValue;
                option.textContent = optionValue;
                selectElement.appendChild(option);
            });
            selectElement.disabled = isDisabled;
        }
    }

    ['option', 'vertical', 'condor'].forEach(prefix => {
        const form = new TradeForm(prefix);
        form.init();
    });

    // --- Script to reinitialize MDB components on tab change ---
    const tradeTabLinks = document.querySelectorAll('#trade-tabs a[data-mdb-tab-init]');
    tradeTabLinks.forEach(tab => {
        tab.addEventListener('shown.mdb.tab', (event) => {
            const paneId = event.target.getAttribute('href');
            const pane = document.querySelector(paneId);
            if (pane) {
                pane.querySelectorAll('[data-mdb-input-init]').forEach((input) => {
                    new mdb.Input(input).init();
                });
            }
        });
    });
});
