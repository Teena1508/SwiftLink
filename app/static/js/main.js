document.addEventListener('DOMContentLoaded', () => {
  // 1. Shorten Form Handler
  const shortenForm = document.getElementById('shorten-form');
  if (shortenForm) {
    shortenForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const urlInput = document.getElementById('url-input');
      const aliasInput = document.getElementById('alias-input');
      const ttlInput = document.getElementById('ttl-input');
      const resultCard = document.getElementById('result-card');
      const errorBox = document.getElementById('form-error');

      errorBox.style.display = 'none';
      errorBox.textContent = '';

      const payload = {
        url: urlInput.value.trim()
      };

      if (aliasInput && aliasInput.value.trim()) {
        payload.custom_alias = aliasInput.value.trim();
      }

      if (ttlInput && ttlInput.value.trim()) {
        payload.ttl_seconds = parseInt(ttlInput.value.trim(), 10);
      }

      try {
        const response = await fetch('/shorten', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
          errorBox.textContent = data.message || 'An error occurred while shortening the URL.';
          errorBox.style.display = 'block';
          return;
        }

        // Display Success Result
        const shortUrlLink = document.getElementById('short-url-link');
        const originalUrlText = document.getElementById('original-url-text');
        const shortCodeText = document.getElementById('short-code-text');

        shortUrlLink.href = data.short_url;
        shortUrlLink.textContent = data.short_url;
        originalUrlText.textContent = data.original_url;
        shortCodeText.textContent = data.short_code;

        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth' });
      } catch (err) {
        errorBox.textContent = 'Network error. Failed to reach server.';
        errorBox.style.display = 'block';
      }
    });
  }
});

// Copy to Clipboard Utility
function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    const originalText = btnElement.textContent;
    btnElement.textContent = 'Copied! ✓';
    btnElement.style.background = '#10b981';
    setTimeout(() => {
      btnElement.textContent = originalText;
      btnElement.style.background = '';
    }, 2000);
  }).catch(err => {
    alert('Failed to copy to clipboard.');
  });
}

// Delete Short URL Handler using API Key
async function deleteUrl(shortCode, apiKey) {
  if (!confirm(`Are you sure you want to delete short code '${shortCode}'?`)) {
    return;
  }

  try {
    const response = await fetch(`/${shortCode}`, {
      method: 'DELETE',
      headers: {
        'X-API-Key': apiKey,
        'Accept': 'application/json'
      }
    });

    const data = await response.json();

    if (response.ok) {
      alert(data.message || 'Short code deleted successfully.');
      window.location.reload();
    } else {
      alert(`Delete failed: ${data.message || 'Unauthorized'}`);
    }
  } catch (err) {
    alert('Network error while deleting URL.');
  }
}
