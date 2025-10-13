/**
 * Initialize Select2 on a customer selection field
 * @param {string} selector - jQuery selector for the field
 * @param {object} options - Configuration options
 * @param {string} options.searchUrl - URL for AJAX search
 * @param {object} options.initialCustomer - Initial customer data (id, text, icon, color, exempted)
 * @param {string} options.placeholder - Placeholder text
 * @param {string} options.language - Language code for Select2
 */
function initCustomerSelect2(selector, options = {}) {
    const defaults = {
        searchUrl: '/search-customers/',
        initialCustomer: null,
        placeholder: 'Search for a customer...',
        language: 'en-GB'
    };

    const config = {...defaults, ...options};

    // Initialize Select2
    $(selector).select2({
        placeholder: config.placeholder,
        allowClear: true,
        width: '100%',
        language: config.language,
        ajax: {
            url: config.searchUrl,
            dataType: 'json',
            delay: 300,
            data: function (params) {
                return {
                    q: params.term || ''
                };
            },
            processResults: function (data) {
                return {
                    results: data.results
                };
            }
        },
        templateResult: formatClient,
        templateSelection: formatClientSelection
    });

    // Load initial value if provided
    if (config.initialCustomer) {
        const option = new Option(
            config.initialCustomer.text,
            config.initialCustomer.id,
            true,
            true
        );
        $(selector).append(option).trigger('change');
        $(selector).data('customer-data', config.initialCustomer);
    }

    /**
     * Format customer for dropdown results
     * @param {object} client - Customer data
     * @returns {jQuery|string} Formatted HTML element
     */
    function formatClient(client) {
        if (!client.id) return client.text;

        let exemptedBadge = '';
        if (client.exempted) {
            exemptedBadge = '<span class="badge-exemption" title="' +
                config.exemptedTitle + '">' +
                '<i class="fas fa-hand-holding-heart"></i>' +
                '</span> ';
        }

        return $('<div class="select2-result-customer">' + exemptedBadge +
            '<i class="fas ' + client.icon + '" style="color:' +
            client.color + '" title="' + client.type_name + '"></i> ' +
            client.text +
            '</div>');
    }

    /**
     * Format customer for selected item
     * @param {object} client - Customer data
     * @returns {jQuery|string} Formatted HTML element
     */
    function formatClientSelection(client) {
        // Use stored data if available
        if (client.id && !client.icon) {
            const storedData = $(selector).data('customer-data');
            if (storedData && storedData.id == client.id) {
                client = storedData;
            }
        }

        let exemptedBadge = '';
        if (client.exempted) {
            exemptedBadge = '<span class="badge-exemption" title="' +
                config.exemptedTitle + '">' +
                '<i class="fas fa-hand-holding-heart"></i>' +
                '</span> ';
        }

        return $('<div class="select2-result-customer">' + exemptedBadge +
            '<i class="fas ' + client.icon + '" style="color:' +
            client.color + '" title="' + client.type_name + '"></i> ' +
            client.text +
            '</div>');
    }
}
