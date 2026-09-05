async (page) => {
  const base = 'http://127.0.0.1:8767';
  const checks = [], errors = [], missing = [];
  await page.unroute('**/api');
  const check = (ok, label) => { if (!ok) throw Error(label); checks.push(label); };
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => { if (response.url().includes('/assets/') && response.status() >= 400) missing.push(response.url()); });
  await page.goto(base);
  await page.evaluate(() => { sessionStorage.clear(); localStorage.setItem('drsk-language', 'en'); localStorage.setItem('niyet-theme', 'dark'); });
  await page.reload();
  await page.setViewportSize({width:1366,height:900});
  await page.locator('#pipelineState.live').waitFor({timeout:30000});
  await page.locator('#startContext').click();
  check(await page.locator('#composerText').evaluate(el=>el===document.activeElement), 'Primary CTA focuses real composer');
  await page.locator('#sourcechainGuide summary').click();
  check(await page.locator('.chain-steps li').count()===5, 'SOURCECHAIN has five semantic explanation steps');
  await page.screenshot({path:'output/qa/polish-sourcechain.png',fullPage:true});
  await page.locator('#sourcechainGuide summary').click();
  await page.locator('[data-theme-toggle]').click();
  check(await page.locator('html').getAttribute('data-theme')==='light', 'Appearance switches to light');
  await page.goto(base+'/lab');
  check(await page.locator('html').getAttribute('data-theme')==='light', 'Appearance persists across routes');
  await page.locator('#labApiStatus.ok').waitFor({timeout:30000});
  await page.screenshot({path:'output/qa/polish-lab-light.png',fullPage:true});
  await page.locator('[data-theme-toggle]').click();
  await page.goto(base+'/?open=evidence');
  await page.locator('#evidenceCard:not([hidden])').waitFor({timeout:30000});
  await page.locator('#evidenceToggle').click();
  check(await page.locator('#evidenceTrail li').count()===4, 'Evidence trail comes from analyzed payload');
  check((await page.locator('#resolutionStatus strong').innerText()).length>5, 'Resolution has human-readable label');
  await page.locator('.source-provenance summary').first().click();
  check((await page.locator('.source-provenance dd').allTextContents()).some(v=>v.length>=64), 'Full document fingerprint is accessible');
  await page.locator('.analysis-notes summary').click();
  check((await page.locator('.analysis-notes p').innerText()).length>20, 'Original backend explanation remains accessible');
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'output/qa/polish-evidence.png',fullPage:true});
  // Delay only genuine requests, then abort a draft before analysis finishes.
  await page.route('**/api', async route => {
    if (route.request().method()==='POST') await page.waitForTimeout(700);
    await route.continue();
  });
  await page.locator('[data-demo="help"]').click();
  await page.locator('#analysisProgress').waitFor();
  check(await page.locator('.composer').getAttribute('aria-busy')==='true', 'Analysis reports loading accessibly');
  await page.locator('#composerText').fill('Short');
  check(await page.locator('#analysisProgress').isHidden(), 'Replacing draft clears stale progress');
  await page.waitForTimeout(800);
  await page.unroute('**/api');
  await page.route('**/api', route=>route.fulfill({status:503,contentType:'application/json',body:'{}'}));
  await page.locator('[data-demo="help"]').click();
  await page.locator('#analysisError').waitFor();
  check((await page.locator('#analysisError').innerText()).includes('Your draft is safe'), 'Failure keeps draft and explains recovery');
  await page.unroute('**/api');
  await page.locator('#retryAnalysis').click();
  await page.locator('#pipelineState.live').waitFor({timeout:30000});
  await page.locator('#intentPanel.visible').waitFor({timeout:30000});
  check(await page.locator('#analysisError').isHidden(), 'Retry restores real analysis');
  await page.locator('#composerText').fill('');
  const routes=['/','/#explore','/#communities','/#messages','/#profile','/lab'];
  for (const width of [375,768,1366,1440,1920]) {
    await page.setViewportSize({width,height:width===375?812:900});
    for (const [index,route] of routes.entries()) {
      await page.goto(base+route);
      if(route==='/lab') await page.locator('#labApiStatus.ok').waitFor({timeout:30000});
      check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${route} fits ${width}px`);
      if(width===375||width===1366) await page.screenshot({path:`output/qa/polish-route-${index}-${width}.png`,fullPage:true});
    }
  }
  await page.goto(base+'/#explore');
  await page.locator('#exploreSearch').fill('zz-no-matches');
  await page.locator('.clear-search').click();
  check(await page.locator('#searchResults .post-card').count()>0,'Empty search has working clear action');
  await page.goto(base+'/#messages');
  await page.locator('.empty-action').click();
  check(await page.locator('#composerText').isVisible(),'Empty messages has working return action');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('[data-demo="help"]').click();
  check(await page.locator('.progress-line').evaluate(el=>getComputedStyle(el,'::after').animationName)==='none','Reduced motion disables progress animation');
  await page.emulateMedia({reducedMotion:'no-preference'});
  check(missing.length===0,'No asset 404s');
  check(errors.length===0,'No uncaught JavaScript errors');
  await page.setViewportSize({width:1366,height:900});
  await page.goto(base);
  return {passed:checks.length,checks,errors,missing};
}
