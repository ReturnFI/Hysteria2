    document.addEventListener("DOMContentLoaded", function() {
      const urlParams = new URLSearchParams(window.location.search);
      const activeTab = urlParams.get('tab');
      if (activeTab === 'users') {
        $('.nav-pills a[href="#users"]').tab('show');
      }
    });
    function generateQRCodes(qrDataIPv4, qrDataIPv6) {
        if (qrDataIPv4) {
            const qrCodeIPv4 = new QRious({
                element: document.getElementById('qrCodeCanvasIPv4'),
                value: qrDataIPv4,
                size: 200
            });
            document.getElementById('qrCodeTextIPv4').textContent = qrDataIPv4;
        } else {
            document.getElementById('qrCodeCanvasIPv4').getContext('2d').clearRect(0, 0, 200, 200);
            document.getElementById('qrCodeTextIPv4').textContent = "No IPv4 QR code available.";
        }

        if (qrDataIPv6) {
            const qrCodeIPv6 = new QRious({
                element: document.getElementById('qrCodeCanvasIPv6'),
                value: qrDataIPv6,
                size: 200
            });
            document.getElementById('qrCodeTextIPv6').textContent = qrDataIPv6;
        } else {
            document.getElementById('qrCodeCanvasIPv6').getContext('2d').clearRect(0, 0, 200, 200);
            document.getElementById('qrCodeTextIPv6').textContent = "No IPv6 QR code available.";
        }
    }
    function confirmReset(event) {
        const confirmed = confirm("Are you sure you want to reset this user?");
        if (!confirmed) {
            event.preventDefault();
        }
    }

    function confirmRemove(event) {
        const confirmed = confirm("Are you sure you want to remove this user?");
        if (!confirmed) {
            event.preventDefault();
        }
    }

    function refreshUsers() {
      window.location.href = "/dashboard?tab=users";
    }
