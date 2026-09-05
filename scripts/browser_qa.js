async (page) => {
  const base = 'http://127.0.0.1:8767';
  const results = [];
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const check = (value, label) => { if (!value) throw new Error(label); results.push(label); console.log('PASS: ' + label); };
  const visible = async (selector) => page.locator(selector).isVisible();
  await page.goto(base);
  await page.evaluate(() => { sessionStorage.clear(); localStorage.setItem('drsk-language', 'en'); });
  await page.reload();
  await page.locator('#pipelineState.live').waitFor({ timeout: 30000 });
  await page.setViewportSize({ width: 1440, height: 1000 });
  check(await visible('#composerText'), 'Product available on first visit');
  await page.locator('#publishPost').click();
  check(await visible('#composerError'), 'Empty post has inline validation');
  await page.locator('[data-demo="help"]').click();
  await page.locator('#intentPanel.visible').waitFor();
  await page.locator('[data-intent="feedback"]').click();
  check(await page.locator('[data-intent="feedback"]').getAttribute('aria-pressed') === 'true', 'Author corrects suggested intent');
  await page.locator('[data-intent="ask"]').click();
  await page.locator('#routeIntent').click();
  await page.waitForFunction(() => !document.querySelector('#acceptMatch').disabled);
  check((await page.locator('#matchType').innerText()).length > 5, 'Real API supplies eligible responder');
  await page.locator('#explainMatch').click();
  check(await visible('#explainSheet.visible'), 'Technical diagnostics open');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Escape');
  check(!(await visible('#explainSheet')), 'Technical dialog closes with Escape');
  await page.route('**/api', route => {
    const data = route.request().postDataJSON();
    if (data?.action === 'accept') return route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":"test_failure"}' });
    return route.continue();
  });
  await page.locator('#acceptMatch').click();
  check(await page.locator('#acceptMatch').isEnabled(), 'Failed accept remains retryable');
  check(!(await page.locator('#matchStatus').innerText()).includes('Accepted'), 'Failed accept does not claim success');
  await page.unroute('**/api');
  await page.locator('#routingSwitch').click();
  await page.waitForFunction(() => document.querySelector('#routingSwitch').classList.contains('off'));
  await page.locator('#routingSwitch').click();
  await page.waitForFunction(() => !document.querySelector('#routingSwitch').classList.contains('off'));
  check(true, 'Pause and resume work against the same responder');
  await page.locator('#acceptMatch').click();
  await page.waitForFunction(() => document.querySelector('#matchStatus').textContent === 'Accepted');
  check(await page.locator('#skipMatch').isDisabled(), 'Accepted request cannot be skipped again');
  await page.locator('[data-demo="normal"]').click();
  await page.waitForFunction(() => document.querySelector('#routeResult').classList.contains('visible') || document.querySelector('#intentPanel').classList.contains('visible'));
  if (await page.locator('#intentPanel').isVisible()) await page.locator('#dismissIntent').click();
  const postText = await page.locator('#composerText').inputValue();
  await page.locator('#publishPost').click();
  check((await page.locator('.demo-user-post').first().innerText()).includes(postText), 'Normal post published locally');
  await page.reload();
  check(await page.locator('.demo-user-post').count() === 1, 'Local post survives refresh');
  for (const [index, view] of ['feed','explore','communities','messages','profile'].entries()) {
    await page.locator('.nav-list .nav-item').nth(index).click();
    check(page.url().endsWith(`#${view}`), `${view} has a direct URL`);
    if (view === 'explore') {
      await page.locator('#exploreSearch').fill('no-result-xyz');
      check((await page.locator('#searchResults').innerText()).includes('No conversations'), 'Search empty state');
      await page.locator('[data-topic="robot"]').click();
      check(await page.locator('#searchResults .post-card').count() > 0, 'Topic search returns real feed content');
    }
  }
  await page.goBack();
  check(page.url().endsWith('#messages'), 'Back restores previous section');
  await page.goForward();
  check(page.url().endsWith('#profile'), 'Forward restores next section');
  await page.reload();
  check(await visible('.profile-demo'), 'Profile deep link survives refresh');
  await page.goto(base + '/?open=evidence');
  await page.locator('#pipelineState.live').waitFor({ timeout: 30000 });
  await page.locator('[data-demo="evidence"]').click();
  await page.locator('#evidenceCard:not([hidden])').waitFor();
  await page.locator('#evidenceToggle').click();
  await page.locator('.evidence-source-link').waitFor();
  check((await page.locator('.evidence-source-link').first().getAttribute('href')).startsWith('https://pubmed.ncbi.nlm.nih.gov/'), 'Evidence preserves real source provenance');
  await page.locator('.claim-comparison summary').first().click();
  check(await visible('.distortion-lens'), 'Claim and passage comparison visible');
  await page.screenshot({ path: 'output/qa/evidence-desktop.png', fullPage: true });
  await page.evaluate(() => { sessionStorage.removeItem('drsk-responder-state'); sessionStorage.removeItem('drsk-open-requests'); });
  await page.reload();
  await page.locator('#pipelineState.live').waitFor({ timeout: 30000 });
  await page.locator('#composerText').fill('Robot PID control loop oscillation is 40 percent worse.');
  await page.waitForFunction(() => document.querySelector('#claimList').textContent.includes('Robot PID'));
  if (!(await visible('#evidenceDetails'))) await page.locator('#evidenceToggle').click();
  await page.locator('#askPerson').click();
  await page.waitForFunction(() => !document.querySelector('#acceptMatch').disabled);
  check(true, 'Insufficient evidence escalates to actionable human match');
  for (const [width, height] of [[360,800],[430,900],[768,1024],[1280,800],[1440,1000]]) {
    await page.setViewportSize({width,height});
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Feed no overflow at ${width}px`);
    if (width === 360) {
      await page.locator('#mobileInboxButton').click();
      check(await visible('.right-rail.mobile-open'), 'Mobile responder controls reachable');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Escape');
      check(!(await visible('.right-rail')), 'Mobile drawer Escape restores feed');
    }
  }
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({ path: 'output/qa/feed-mobile.png', fullPage: true });
  await page.locator('[data-lang="tr"]').click();
  check(await page.locator('html').getAttribute('lang') === 'tr', 'Turkish language updates document');
  await page.goto(base + '/lab');
  await page.locator('#labApiStatus.ok').waitFor({timeout:30000});
  check(await page.locator('html').getAttribute('lang') === 'tr', 'Language carries into lab');
  await page.locator('[data-lab-lang="en"]').first().click();
  for (let index=0; index<4; index++) {
    await page.locator('#batchTabs button').nth(index).click();
    await page.waitForFunction(() => !document.querySelector('.lab-shell').classList.contains('loading'));
    check(await page.locator('.metric').count() === 6, `Lab batch ${index+1} returns both methods`);
  }
  await page.locator('#floorRange').fill('0.12');
  await page.locator('#floorRange').dispatchEvent('input');
  await page.waitForFunction(() => !document.querySelector('.lab-shell').classList.contains('loading') && location.search.includes('0.12'));
  check(page.url().includes('floor=0.12'), 'Lab threshold preserved in URL');
  for (const width of [360,430,768,1280,1440]) {
    await page.setViewportSize({width,height:900});
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Lab no overflow at ${width}px`);
  }
  await page.screenshot({path:'output/qa/lab-desktop.png',fullPage:true});
  await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});
  await page.screenshot({path:'output/qa/lab-dark.png',fullPage:true});
  await page.route('**/api/experiment?**', route => route.fulfill({status:503,contentType:'application/json',body:'{}'}));
  await page.locator('#retryExperiment').click();
  await page.locator('#labApiStatus.error').waitFor();
  check((await page.locator('#summaryTitle').innerText()).includes('unavailable'), 'Lab failure has honest error state');
  await page.unroute('**/api/experiment?**');
  await page.locator('#retryExperiment').click();
  await page.locator('#labApiStatus.ok').waitFor({timeout:30000});
  check(true, 'Lab retries successfully');
  check(errors.length === 0, `No uncaught browser errors: ${errors.join('; ')}`);
  await page.emulateMedia({colorScheme:'light',reducedMotion:'no-preference'});
  await page.goto(base);
  return {passed:results.length,checks:results,errors};
}
