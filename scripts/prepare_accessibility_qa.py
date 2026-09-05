import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2:
    raise SystemExit('Usage: python scripts/prepare_accessibility_qa.py PATH_TO_AXE_MIN_JS')
axe = Path(sys.argv[1]).read_text(encoding='utf-8')
code = '''async (page) => {
 const results = [];
 for (const theme of ['light','dark']) {
  await page.emulateMedia({colorScheme:theme});
  for (const route of ['/', '/#explore','/#communities','/#messages','/#profile','/lab']) {
   await page.goto('http://127.0.0.1:8767' + route);
   if (route === '/lab') await page.waitForFunction(() => !document.querySelector('.lab-shell').classList.contains('loading'));
   await page.evaluate(AXE_SOURCE);
   const result = await page.evaluate(async () => {
     const audit = await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});
     return audit.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}));
   });
   results.push({route,theme,violations:result});
  }
 }
 await page.emulateMedia({colorScheme:'light'});
 return results;
}'''.replace('AXE_SOURCE', json.dumps(axe))
(root / 'output' / 'qa' / 'accessibility.js').write_text(code, encoding='utf-8')
