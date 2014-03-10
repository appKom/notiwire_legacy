# Online Notiwire
# Shell script for getting all affiliations
# appKom: appkom@online.ntnu.no

echo ""

# curl fetches options.html from the online-notifier repo
curl -s https://raw.github.com/dotKom/online-notifier/master/options.html |
# grep finds all lines matching values in dropdown menues at the options page
grep "<option value=\".*\">.*</option>" |
# grep again finds all values (affiliation keys) enclosed in those dropdown items
grep -oEi "\".*\"" |
# tr joins all lines by a comma
tr "\\n" "," |
# sed removes all entries after the first hit on "blue" (from the color palette dropdown menu in options.html)
sed 's/"blue".*//' |
# sed adds the DEBUG affiliation which OmegaV uses when testing Notipis
sed -e 's/\(^.*\)/\"DEBUG\",\1/'

echo ""
