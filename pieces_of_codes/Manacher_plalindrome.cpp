//
// 马拉车算法，用于解决回文字符串的问题
//
// http://www.cnblogs.com/grandyang/p/4475985.html
// https://mp.weixin.qq.com/s/j5a_66_am0oIPlPB2BME9g
//

#include <vector>
#include <iostream>
#include <string>

using namespace std;

string Manacher(string s) 
{
    // step 1: Insert '#'
    //
    string t = "$#";
    for (int i = 0; i < s.size(); ++i) 
    {
        t += s[i];
        t += "#";
    }

    // step 2: init p[] all to 0
    //
    vector<int> p(t.size(), 0);

    int mx = 0;
    int id = 0;
    int maxlen = 0;
    int maxlen_pos = 0;

    // step 3: process this string
    //
    for (int i = 1; i < t.size(); ++i) 
    {
        // core code
        //
        p[i] = mx > i ? min(p[2 * id - i], mx - i) : 1;

        // extend in center to left/right, compute the max len
        //
        while (t[i + p[i]] == t[i - p[i]])
        {
            ++p[i];
        }

        if (mx < i + p[i]) 
        {
            // update mx and id
            //
            mx = i + p[i];
            id = i;
        }

        if (maxlen < p[i]) 
        {
            // update maxlen and its position
            //
            maxlen = p[i];
            maxlen_pos = i;
        }
    }

    return s.substr((maxlen_pos - maxlen) / 2, maxlen - 1);
}

int main() 
{
    string s1 = "12212";
    cout << Manacher(s1) << endl;
    string s2 = "122122";
    cout << Manacher(s2) << endl;
    string s = "waabwswfd";
    cout << Manacher(s) << endl;
}