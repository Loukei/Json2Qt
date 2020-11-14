#include "user.h"

QJsonObject parseJsonFile(const QString& filename)
{
    QFile file(filename);
    if(!file.open(QIODevice::ReadOnly)){
        auto msg = QString("File (%1) open fail: %2.").arg(filename,file.errorString());
        qFatal("%s",msg.toStdString().c_str());
        return QJsonObject();
    }

    QJsonParseError jsonErr;
    auto jsonDoc = QJsonDocument::fromJson(file.readAll(),&jsonErr);
    if(jsonErr.error != QJsonParseError::NoError){
        auto msg = QString("File (%1) parse error: %2.").arg(filename,jsonErr.errorString());
        qFatal("%s",msg.toStdString().c_str());
        return QJsonObject();
    }
    return jsonDoc.object();
}

// construct User from QJsonObject,not 
User::User(const QJsonObject &jsonObj)
{
    // parse int userid
    this->userid = jsonObj["userid"].toInt();
    // parse QString username
    this->username = jsonObj["username"].toString();
    // parse bool verified
    this->verified = jsonObj["verified"].toBool();
    // parse double weight
    this->weight = jsonObj["weight"].toDouble();
    // parse QList<int> items
    QJsonArray itemsArray = jsonObj["items"].toArray();
    for(auto i:itemsArray){
        this->items.append(i.toInt());
    }
    // parse QList<QString> games
    QJsonArray gamesArray = jsonObj["games"].toArray();
    for(auto i:gamesArray){
        this->games.append(i.toString());
    }
}

QJsonObject User::toQJsonObject() const
{
    QJsonObject obj;
    obj.insert("userid",this->userid);
    obj.insert("username",this->username);
    obj.insert("verified",this->verified);
    obj.insert("weight",this->weight);
    //fill items
    QJsonArray ItemsArray;
    for(auto i:this->items){
        ItemsArray.append(i);
    }
    obj.insert("items",ItemsArray);
    //fill games
    QJsonArray GamesArray;
    for(auto i:this->games){
        GamesArray.append(i);
    }
    obj.insert("games",GamesArray);
    return obj;
}


