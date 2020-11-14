#include <QCoreApplication>
#include "user.h"

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    QJsonObject jsonObj = parseJsonFile("C:/user.json");
    auto user = User(jsonObj);
    qDebug() << "User:" << user.toQJsonObject();

    return a.exec();
}
