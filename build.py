from pathlib import Path
import html, os, shutil, sys
ROOT=Path(__file__).resolve().parent
SITE=ROOT/"site"
DIST=ROOT/"dist"
fields={
"__TAKENOS_NAME__":"TAKENOS_NAME",
"__TAKENOS_ACH_ACCOUNT__":"TAKENOS_ACH_ACCOUNT",
"__TAKENOS_ACH_ROUTING__":"TAKENOS_ACH_ROUTING",
"__TAKENOS_ACH_ACCOUNT_TYPE__":"TAKENOS_ACH_ACCOUNT_TYPE",
"__TAKENOS_ACH_BANK__":"TAKENOS_ACH_BANK",
"__TAKENOS_ACH_BANK_ADDRESS__":"TAKENOS_ACH_BANK_ADDRESS",
"__TAKENOS_SEPA_IBAN__":"TAKENOS_SEPA_IBAN",
"__TAKENOS_SEPA_BIC__":"TAKENOS_SEPA_BIC",
"__TAKENOS_SEPA_BANK__":"TAKENOS_SEPA_BANK",
"__TAKENOS_SEPA_BANK_ADDRESS__":"TAKENOS_SEPA_BANK_ADDRESS"}
missing=[v for v in fields.values() if not os.environ.get(v)]
if missing:
 print("Build stopped. Missing required GitHub Actions secrets:")
 [print(" -",x) for x in missing]
 sys.exit(1)
t=(SITE/"index.template.html").read_text(encoding="utf-8")
for p,e in fields.items(): t=t.replace(p,html.escape(os.environ[e].strip(),quote=True))
if DIST.exists(): shutil.rmtree(DIST)
DIST.mkdir(parents=True)
(DIST/"index.html").write_text(t,encoding="utf-8")
for n in ("styles.css","app.js","robots.txt"): shutil.copy2(SITE/n,DIST/n)
(DIST/".nojekyll").write_text("",encoding="utf-8")
print("Site built successfully.")
