function clientUrls(extra, platform) {
  const configured = value => typeof value === 'string' && value.trim() ? value.trim() : null;
  return {
    backendUrl: configured(extra?.apiUrl) || `http://${platform === 'android' ? '10.0.2.2' : '127.0.0.1'}:8000`,
    websiteUrl: configured(extra?.siteUrl) || (platform === 'web' && !extra?.production ? 'http://127.0.0.1:5128' : null),
  };
}
module.exports = {clientUrls};
