tmprefix=`date '+20%y-%m-%d'`
this_year=`date '+20%y'`
fname="$tmprefix-titls.md"
touch $fname
echo "---" >> $fname
echo "layout: post" >> $fname
echo "title: " >> $fname
echo "date: $tmprefix" >> $fname
echo "category: ${this_year}年" >> $fname
echo "keywords: " >> $fname
echo "---" >> $fname
