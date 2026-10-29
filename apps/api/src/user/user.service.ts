import { ConflictException, Injectable } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import { PrismaService } from '../prisma/prisma.service';
import { UserEntity } from './entities/user.entity';
import { Prisma } from 'generated/prisma/client';
import { UpdateUserDto } from './dto/update-user.dto';

@Injectable()
export class UserService {
  constructor(private readonly prisma: PrismaService) {}

  async findByEmail(email: string) {
    return await this.prisma.user.findUnique({ where: { email } });
  }

  async create(data: Prisma.UserCreateInput): Promise<UserEntity> {
    try {
      return await this.prisma.user.create({
        data,
        omit: { hashedPassword: true },
      });
    } catch (error) {
      if (
        error instanceof Prisma.PrismaClientKnownRequestError &&
        error.code === 'P2002'
      ) {
        throw new ConflictException('Email is already used');
      }
      throw error;
    }
  }

  async update(id: string, updateUserDto: UpdateUserDto) {
    const data: Prisma.UserUpdateInput = {
      name: updateUserDto.name,
      email: updateUserDto.email,
    };
    if (updateUserDto.password !== undefined) {
      const hashedPassword = await bcrypt.hash(updateUserDto.password, 10);
      data.hashedPassword = hashedPassword;
    }

    return await this.prisma.user.update({
      data,
      where: {
        id,
      },
      omit: { hashedPassword: true },
    });
  }
}
