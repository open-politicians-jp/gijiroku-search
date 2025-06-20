'use client';

import Script from 'next/script';

const GA_TRACKING_ID = 'G-FL3SFH0K42';

export default function GoogleAnalytics() {
  // 本番環境でのみGoogle Analyticsを有効化
  if (process.env.NODE_ENV !== 'production') {
    return null;
  }

  return (
    <>
      <Script
        strategy="afterInteractive"
        src={`https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`}
      />
      <Script
        id="gtag-init"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{
          __html: `
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_TRACKING_ID}', {
              page_title: document.title,
              page_location: window.location.href
            });
          `,
        }}
      />
    </>
  );
}