import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { UserService } from '../user/user.service';
import { LoginDto } from './dto/login.dto';
import { JwtPayload } from './strategies/jwt.strategy';
import { RegisterDto } from './dto/register.dto';
import { UserEntity } from '../user/entities/user.entity';

@Injectable()
export class AuthService {
  constructor(
    private readonly userService: UserService,
    private readonly jwtService: JwtService,
  ) {}

  async register(registerDto: RegisterDto): Promise<UserEntity> {
    const hashedPassword = await bcrypt.hash(registerDto.password, 10);
    return this.userService.create({
      email: registerDto.email,
      name: registerDto.name,
      hashedPassword: hashedPassword,
    });
  }

  async login(loginDto: LoginDto) {
    const ERR_MESSAGE = 'Wrong email or password';
    const user = await this.userService.findByEmail(loginDto.email);
    if (user === null) {
      throw new UnauthorizedException(ERR_MESSAGE);
    }
    const isCorrect = await bcrypt.compare(
      loginDto.password,
      user.hashedPassword,
    );
    if (!isCorrect) {
      throw new UnauthorizedException(ERR_MESSAGE);
    }

    const payload: JwtPayload = {
      sub: user.id,
      email: user.email,
    };
    return this.jwtService.sign(payload, {
      expiresIn: parseInt(process.env.EXPIRY_TIME_MS as string) / 1000, // Takes in seconds
      secret: process.env.JWT_SECRET as string,
    });
  }
}
