import time
from WrSignal import write_sql_err
from nJdbc import get_my_connection

"""执行语句查询有结果返回结果没有返回0；增/删/改返回变更数据条数，没有返回0"""
class MySqLHelper(object):
    def __init__(self):
        self.db = get_my_connection()  # 从数据池中获取连接
        # time.sleep(15)

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'inst'):  # 单例
            cls.inst = super(MySqLHelper, cls).__new__(cls, *args, **kwargs)
        return cls.inst

    # 封装执行命令
    def execute(self, sql, param=None, autoclose=False):
        """
        【主要判断是否有参数和是否执行完就释放连接】
        :param sql: 字符串类型，sql语句
        :param param: sql语句中要替换的参数"select %s from tab where id=%s" 其中的%s就是参数
        :param autoclose: 是否关闭连接
        :return: 返回连接conn和游标cursor
        """
        cursor, conn = self.db.getconn()  # 从连接池获取连接
        count = 0
        try:
            # count : 为改变的数据条数
            if param:
                count = cursor.execute(sql, param)
            else:
                count = cursor.execute(sql)
            conn.commit()
            if autoclose:
                self.close(cursor, conn)
        except Exception as e:
            write_sql_err(e,sql)
            pass
        return cursor, conn, count

    # 释放连接
    def close(self, cursor, conn):
        """释放连接归还给连接池"""
        cursor.close()
        conn.close()

    # 查询所有
    def selectall(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            res = cursor.fetchall()
            return res
        except Exception as e:
            print("查询所有:",e)
            print(sql)
            write_sql_err(e , sql)
            self.close(cursor, conn)
            return count

    # 查询单条
    def selectone(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            res = cursor.fetchone()
            # print(res)
            self.close(cursor, conn)
            return res
        except Exception as e:
            print("查询单条:", e.args)
            print(sql)
            write_sql_err(e ,sql)
            self.close(cursor, conn)
            return count
    # 查询 返回1游标
    def retCursor(self, sql ,param =None ):
        try:
            cursor, conn, count = self.execute(sql, param)
            res = cursor.fetchone()
            self.close(cursor, conn)
            return res
        except Exception as e:
            print("查询单条:", e.args)
            print(sql)
            write_sql_err(e ,sql)
            self.close(cursor, conn)
            return cursor

    # 增加
    def zhix(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            r_id = cursor.lastrowid  # 获取当前插入数据的主键id，该id应该为自动生成为好
            conn.commit()
            self.close(cursor, conn)
            # return count
            # 防止表中没有id返回0
            # print(r_id)
            if r_id == 0:
                return True
            return r_id
        except Exception as e:
            print('添加数据库：',e)
            write_sql_err(e,sql)
            print(sql)
            conn.rollback()
            self.close(cursor, conn)
            return count

    # 增加多行
    def insertmany(self, sql, param):
        """
        :param sql:
        :param param: 必须是元组或列表[(),()]或（（），（））
        :return:
        """
        cursor, conn, count = self.db.getconn()
        try:
            cursor.executemany(sql, param)
            conn.commit()
            return count
        except Exception as e:
            print("增加多行:",e)
            print(sql)
            write_sql_err(e , sql)
            conn.rollback()
            self.close(cursor, conn)
            return count

    # 删除
    def delete(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            self.close(cursor, conn)
            return count
        except Exception as e:
            print("删除:",e)
            print(sql)
            write_sql_err(e , sql)
            conn.rollback()
            self.close(cursor, conn)
            return count

    # 更新
    def update(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            conn.commit()
            self.close(cursor, conn)
            return count
        except Exception as e:
            print("更新:", e)
            print(sql)
            conn.rollback()
            self.close(cursor, conn)
            write_sql_err(e , sql)
            return count

    def repNulletition(self,sql):
        pass

        # if req = None:
        #     return False


if __name__ == '__main__':
    # db = MySqLHelper()
    # while True:
    db = MySqLHelper()
    # # 查询单条
    sql1 = 'SELECT * FROM m_list where id = 0'
    args = 'python'
    ret = db.selectone(sql=sql1)
    print(ret)  # (None, b'python', b'123456', b'0')
    time.sleep(0.8)
    # db.close()
