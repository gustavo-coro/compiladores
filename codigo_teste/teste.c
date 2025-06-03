void add(int a, int b) {
    return a + b;
}

int main() {
    char** str = "exemplo";
    int* i = 8;
    int a = 10;
    float pi = 3.14;
    char car = 'c';
    int c=0xFAFA;
    a = 5;
    if (&a == i) {
        a = 10;
    }
    int b = 6;
    for (a = 0; b < a; a++);
    int i = 15; //comentario
    while (i || 0) {
        i--;
        /*funcao que nao faz 
        sentido*/
        add(i, a);
    }
    do {
        i+=2;
    } while (i < 15);

    int d = a > b ? a : b;

    return 0;
}