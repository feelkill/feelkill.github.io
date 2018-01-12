//
// Aho-Corasick 算法
// 字符串的多模式匹配算法
//
// https://mp.weixin.qq.com/s/0AIVHUN8XrSnRKmo9Jwpng
//

#include <iostream>
#include <queue>

#define TREE_WIDTH 26

using namespace std;

struct Node
{
    int end;
    Node * fail;
    Node * next[TREE_WIDTH];
    Node()
    {
        this->end = 0;
        this->fail = nullptr;
        for (int i = 0; i < TREE_WIDTH; i++)
            this->next[i] = nullptr;
    }
};

class AC
{
private:
    Node * root;
public:
    AC();
    ~AC();
    void destroy(Node * t);
    void add(char * s);
    void build_fail_pointer();
    int ac_automaton(char * t);
};

AC::AC()
{
    root = new Node;
}

AC::~AC()
{
    destroy(root);
}

void AC::destroy(Node * t)
{
    for (int i = 0; i < TREE_WIDTH; i++)
        if (t->next[i])
            destroy(t->next[i]);
    delete t;
}

void AC::add(char * s)
{
    Node * t = root;
    while (*s)
    {
        if (t->next[*s - 'a'] == nullptr)
            t->next[*s - 'a'] = new Node;
        t = t->next[*s - 'a'];
        s++;
    }
    t->end++;  // 假设单词可重复
}

void AC::build_fail_pointer()
{
    queue<Node*> Q;

    for (int i = 0; i < TREE_WIDTH; i++)
    {
        if (root->next[i])
        {
            Q.push(root->next[i]);
            root->next[i]->fail = root;
        }
    }

    Node * parent = nullptr;
    Node * son = nullptr;
    Node * p = nullptr;
    while (!Q.empty())
    {
        parent = Q.front();
        Q.pop();
        for (int i = 0; i < TREE_WIDTH; i++)
        {
            if (parent->next[i])
            {
                Q.push(parent->next[i]);
                son = parent->next[i];
                p = parent->fail;
                while (p)
                {
                    if (p->next[i])
                    {
                        son->fail = p->next[i];
                        break;
                    }
                    p = p->fail;
                }
                if (!p)  son->fail = root;
            }
        }
    }
}

int AC::ac_automaton(char * t)
{
    int ans = 0;

    int pos;
    Node * pre = root;
    Node * cur = nullptr;
    while (*t)
    {
        pos = *t - 'a';
        if (pre->next[pos])
        {
            cur = pre->next[pos];
            while (cur != root)
            {
                if (cur->end >= 0)
                {
                    ans += cur->end;
                    cur->end = -1;  // 避免重复查找
                }
                else
                    break;  // 等于 -1 说明以前这条路径已找过，现在无需再找
                cur = cur->fail;
            }
            pre = pre->next[pos];
            t++;
        }
        else
        {
            if (pre == root)
                t++;
            else
                pre = pre->fail;
        }
    }
    return ans;
}

int main()
{
    int n;
    char s[1000];
    while (1)
    {
        cout << "请输入单词个数：";
        // n --> 2
        //
        cin >> n;

        AC tree;
        cout << "请输入" << n << "个单词：\n";
        while (n--)
        {
            cin >> s;
            // sher
            // he
            tree.add(s);
        }
      
        cout << "请输入搜索文本：";
        // sher
        //
        cin >> s;
      
        tree.build_fail_pointer();
        cout << "共有" << tree.ac_automaton(s) << "个单词匹配" << endl << endl;
    }
    return 0;
}